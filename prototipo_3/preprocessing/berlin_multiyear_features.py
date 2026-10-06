"""Build and audit a multi-year Berlin HV/temperature feature table.

The script is the ingestion gate for the 2020-2024 experiment. It creates a
canonical UTC index from raw Stromnetz Berlin quarter-hour row order, keeps the
published local labels only as an audit comparison, joins DWD hourly
temperature and writes a reportable audit. It does not train the MLP.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[2]
UTC = timezone.utc
LOCAL_TZ = ZoneInfo("Europe/Berlin")
DEFAULT_YEARS = (2020, 2021, 2022, 2023, 2024)
DEFAULT_HV_ROOT = REPO / "prototipo_3/data/de_alemania/external_validation/berlin_multiyear/hv"
DEFAULT_DWD = REPO / "prototipo_3/data/de_alemania/external_validation/berlin_2024/stundenwerte_TU_00433_hist.zip"
DEFAULT_OUTPUT_ROOT = REPO / "prototipo_3/data/de_alemania/berlin_multiyear"
DEFAULT_REPORT_ROOT = REPO / "corfo-report/validation/berlin/multiyear_2020_2024"
HV_DATE_RE = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")
HV_TIME_RE = re.compile(r"^\d{2}:\d{2}$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def expected_hours(year: int) -> int:
    return 8784 if is_leap(year) else 8760


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp without timezone: {value}")
    return parsed.astimezone(UTC)


def parse_power(value: str) -> float:
    return float(value.strip().replace(".", "").replace(",", "."))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def find_hv_source(year: int, hv_root: Path) -> Path:
    candidates = [
        hv_root / f"Jahreshoechstlast-{year}-Hochspannung.csv",
        hv_root / f"jahreshoechstlast-{year}-hochspannung.csv",
        REPO / f"prototipo_3/data/de_alemania/external_validation/berlin_{year}/Jahreshoechstlast-{year}-Hochspannung.csv",
        REPO / f"prototipo_3/data/de_alemania/external_validation/berlin_{year}/jahreshoechstlast-{year}-hochspannung.csv",
        REPO / f"prototipo_3/data/de_alemania/berlin_hv_{year}/berlin_hv_{year}_hourly.csv",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"No HV input found for {year}: {candidates}")


def read_normalized_hourly(path: Path, year: int) -> tuple[list[dict[str, object]], dict[str, object]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"timestamp_hour_end_utc", "load_mean_MW", "energy_MWh"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Normalized HV file lacks {sorted(required)}: {path}")
        rows = []
        for source_row, row in enumerate(reader, start=2):
            stamp = parse_utc(row["timestamp_hour_end_utc"])
            rows.append({
                "year": year,
                "timestamp_hour_end_utc": stamp.isoformat(),
                "timestamp_hour_end_local": stamp.astimezone(LOCAL_TZ).isoformat(),
                "load_mean_MW": float(row["load_mean_MW"]),
                "energy_MWh": float(row["energy_MWh"]),
                "source_row_start": row.get("source_row_start", source_row),
                "source_row_end": row.get("source_row_end", source_row),
            })
    if len(rows) != expected_hours(year):
        raise ValueError(f"Expected {expected_hours(year)} hourly rows for {year}, got {len(rows)}")
    stamps = [parse_utc(row["timestamp_hour_end_utc"]) for row in rows]
    if len(stamps) != len(set(stamps)):
        raise ValueError(f"Duplicate normalized UTC timestamps for {year}")
    gaps = sum(right - left != timedelta(hours=1) for left, right in zip(stamps, stamps[1:]))
    return rows, {
        "source_kind": "normalized_hourly",
        "quarter_hour_rows": "not_available",
        "timestamp_label_mismatch_count": "not_available",
        "utc_contiguous": gaps == 0,
        "utc_gap_count": gaps,
        "declared_max_kW": "",
        "declared_energy_kWh": "",
    }


def read_raw_hv(path: Path, year: int) -> tuple[list[dict[str, object]], dict[str, object]]:
    quarter_hours: list[tuple[int, datetime, float]] = []
    declared_max = ""
    declared_energy = ""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for source_row, row in enumerate(csv.reader(handle, delimiter=";"), start=1):
            if len(row) >= 3 and row[0].strip() == "Max in kW":
                declared_max = row[2].strip()
            if len(row) >= 3 and row[0].strip() == "Arbeit in kWh":
                declared_energy = row[2].strip()
            if len(row) < 3:
                continue
            date_text, time_text, power_text = (cell.strip() for cell in row[:3])
            if not HV_DATE_RE.fullmatch(date_text) or not HV_TIME_RE.fullmatch(time_text):
                continue
            published = datetime.strptime(f"{date_text} {time_text}", "%d.%m.%Y %H:%M")
            quarter_hours.append((source_row, published, parse_power(power_text)))

    expected_qh = expected_hours(year) * 4
    if len(quarter_hours) != expected_qh:
        raise ValueError(f"Expected {expected_qh} quarter-hours for {year}, got {len(quarter_hours)}")
    first_utc = datetime(year, 1, 1, 0, 15, tzinfo=LOCAL_TZ).astimezone(UTC)
    normalized = []
    mismatch_count = 0
    for position, (source_row, published, power_kw) in enumerate(quarter_hours):
        stamp = first_utc + timedelta(minutes=15 * position)
        local = stamp.astimezone(LOCAL_TZ)
        mismatch = int(published != local.replace(tzinfo=None))
        mismatch_count += mismatch
        normalized.append((source_row, stamp, power_kw))

    hourly = []
    for start in range(0, len(normalized), 4):
        group = normalized[start:start + 4]
        last = group[-1][1]
        powers = [item[2] for item in group]
        hourly.append({
            "year": year,
            "timestamp_hour_end_utc": last.isoformat(),
            "timestamp_hour_end_local": last.astimezone(LOCAL_TZ).isoformat(),
            "load_mean_MW": sum(powers) / 4.0 / 1000.0,
            "energy_MWh": sum(powers) * 0.25 / 1000.0,
            "source_row_start": group[0][0],
            "source_row_end": group[-1][0],
        })
    stamps = [parse_utc(row["timestamp_hour_end_utc"]) for row in hourly]
    gaps = sum(right - left != timedelta(hours=1) for left, right in zip(stamps, stamps[1:]))
    return hourly, {
        "source_kind": "raw_quarter_hour",
        "quarter_hour_rows": len(quarter_hours),
        "timestamp_label_mismatch_count": mismatch_count,
        "utc_contiguous": gaps == 0,
        "utc_gap_count": gaps,
        "declared_max_kW": declared_max,
        "declared_energy_kWh": declared_energy,
    }


def read_hv(path: Path, year: int) -> tuple[list[dict[str, object]], dict[str, object]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        first_line = handle.readline()
    if "timestamp_hour_end_utc" in first_line:
        return read_normalized_hourly(path, year)
    return read_raw_hv(path, year)


def dwd_member(archive: zipfile.ZipFile) -> str:
    candidates = [
        name for name in archive.namelist()
        if Path(name).name.startswith("produkt_tu_stunde_") and name.endswith(".txt")
    ]
    if len(candidates) != 1:
        raise ValueError(f"Expected one DWD hourly product member, got {candidates}")
    return candidates[0]


def read_dwd(path: Path, years: set[int]) -> tuple[dict[datetime, float | None], dict[str, object]]:
    values: dict[datetime, float | None] = {}
    missing = {year: 0 for year in years}
    counts = {year: 0 for year in years}
    with zipfile.ZipFile(path) as archive:
        member = dwd_member(archive)
        with archive.open(member) as binary:
            reader = csv.DictReader((line.decode("latin-1") for line in binary), delimiter=";")
            for row in reader:
                text = row["MESS_DATUM"].strip()
                if len(text) != 10 or not text.isdigit():
                    continue
                year = int(text[:4])
                if year not in years:
                    continue
                stamp = datetime.strptime(text, "%Y%m%d%H").replace(tzinfo=UTC)
                raw = row["TT_TU"].strip()
                value = None if raw.startswith("-999") else float(raw)
                if stamp in values:
                    raise ValueError(f"Duplicate DWD timestamp {stamp}")
                values[stamp] = value
                counts[year] += 1
                missing[year] += int(value is None)
    for year in years:
        if counts[year] != expected_hours(year):
            raise ValueError(f"Expected {expected_hours(year)} DWD rows for {year}, got {counts[year]}")
        stamps = sorted(stamp for stamp in values if stamp.year == year)
        if any(right - left != timedelta(hours=1) for left, right in zip(stamps, stamps[1:])):
            raise ValueError(f"DWD UTC sequence is not continuous for {year}")
    return values, {
        "archive_sha256": sha256(path),
        "member": member,
        "rows_by_year": counts,
        "missing_by_year": missing,
        "source_time_basis": "UTC from DWD MESS_DATUM",
    }


def build_features(hourly_by_year: dict[int, list[dict[str, object]]], temperatures: dict[datetime, float | None]) -> tuple[list[dict[str, object]], dict[int, int]]:
    rows = []
    complete_by_year = {year: 0 for year in hourly_by_year}
    for year in sorted(hourly_by_year):
        for demand in hourly_by_year[year]:
            stamp = parse_utc(demand["timestamp_hour_end_utc"])
            lag_values = [temperatures.get(stamp - timedelta(hours=lag)) for lag in range(8)]
            complete = int(all(value is not None for value in lag_values))
            complete_by_year[year] += complete
            row = {
                "source_year": year,
                "timestamp_hour_end_utc": stamp.isoformat(),
                "timestamp_hour_end_local": stamp.astimezone(LOCAL_TZ).isoformat(),
                "load_mean_MW": f"{float(demand['load_mean_MW']):.9f}",
                "energy_MWh": f"{float(demand['energy_MWh']):.9f}",
                "temperature_missing_any": int(not complete),
                "temperature_complete_8lags": complete,
            }
            for lag, value in enumerate(lag_values):
                row[f"temperature_t_minus_{lag}_C"] = "" if value is None else f"{value:.1f}"
            rows.append(row)
    return rows, complete_by_year


def parse_years(value: str) -> tuple[int, ...]:
    years = tuple(sorted({int(item.strip()) for item in value.split(",") if item.strip()}))
    if not years:
        raise ValueError("At least one year is required")
    return years


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", default=",".join(map(str, DEFAULT_YEARS)))
    parser.add_argument("--hv-root", type=Path, default=DEFAULT_HV_ROOT)
    parser.add_argument("--dwd", type=Path, default=DEFAULT_DWD)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    args = parser.parse_args()
    years = parse_years(args.years)
    hv_root = args.hv_root.resolve()
    dwd_path = args.dwd.resolve()
    output_root = args.output_root.resolve()
    report_root = args.report_root.resolve()
    if not dwd_path.is_file():
        raise FileNotFoundError(dwd_path)

    hourly_by_year = {}
    audit_rows = []
    source_paths = {}
    source_audits = {}
    for year in years:
        source_path = find_hv_source(year, hv_root)
        hourly, source_audit = read_hv(source_path, year)
        hourly_by_year[year] = hourly
        source_paths[year] = source_path
        source_audits[year] = source_audit
        computed_mwh = sum(float(row["energy_MWh"]) for row in hourly)
        declared_text = source_audit["declared_energy_kWh"]
        declared = "" if declared_text == "" else parse_power(str(declared_text))
        comparison = "" if declared == "" else (computed_mwh * 1000.0 - declared) / declared * 100.0
        audit_rows.append({
            "year": year,
            "hv_source": str(source_path.relative_to(REPO)),
            "hv_source_sha256": sha256(source_path),
            "source_kind": source_audit["source_kind"],
            "expected_hours": expected_hours(year),
            "observed_hours": len(hourly),
            "expected_quarter_hour_rows": expected_hours(year) * 4,
            "observed_quarter_hour_rows": source_audit["quarter_hour_rows"],
            "timestamp_label_mismatch_count": source_audit["timestamp_label_mismatch_count"],
            "utc_contiguous": source_audit["utc_contiguous"],
            "utc_gap_count": source_audit["utc_gap_count"],
            "computed_energy_GWh": f"{computed_mwh / 1000.0:.9f}",
            "declared_energy_GWh": "" if declared == "" else f"{declared / 1_000_000.0:.9f}",
            "computed_vs_declared_pct": "" if comparison == "" else f"{comparison:.9f}",
        })

    dwd_years = set(years) | {min(years) - 1}
    temperatures, dwd_audit = read_dwd(dwd_path, dwd_years)
    feature_rows, complete_by_year = build_features(hourly_by_year, temperatures)
    output_root.mkdir(parents=True, exist_ok=True)
    features_path = output_root / "berlin_hv_temperature_features_2020_2024.csv"
    feature_fields = [
        "source_year", "timestamp_hour_end_utc", "timestamp_hour_end_local",
        "load_mean_MW", "energy_MWh",
        *[f"temperature_t_minus_{lag}_C" for lag in range(8)],
        "temperature_missing_any", "temperature_complete_8lags",
    ]
    write_csv(features_path, feature_rows, feature_fields)

    for row in audit_rows:
        year = int(row["year"])
        row["dwd_rows"] = dwd_audit["rows_by_year"][year]
        row["dwd_missing_temperature_rows"] = dwd_audit["missing_by_year"][year]
        row["complete_8lag_rows"] = complete_by_year[year]
        row["excluded_8lag_rows"] = expected_hours(year) - complete_by_year[year]
        row["complete_8lag_pct"] = f"{complete_by_year[year] / expected_hours(year) * 100.0:.9f}"
    audit_path = report_root / "berlin_multiyear_source_audit.csv"
    write_csv(audit_path, audit_rows, list(audit_rows[0]))

    manifest = {
        "dataset": "berlin_hv_temperature_features_2020_2024",
        "status": "ingestion_audit_ready; training_contract_not_created",
        "years": list(years),
        "inputs": {
            "hv": [
                {"year": year, "path": str(source_paths[year].relative_to(REPO)), "sha256": sha256(source_paths[year]), **source_audits[year]}
                for year in years
            ],
            "dwd": {
                "path": str(dwd_path.relative_to(REPO)),
                **dwd_audit,
                "years_included_for_lags": sorted(dwd_years),
            },
        },
        "canonicalization": {
            "timezone_index": "UTC",
            "local_timezone": "Europe/Berlin",
            "raw_hv_rule": "first published 00:15 local plus 15 minutes by source row order; published labels retained for mismatch audit",
            "raw_hv_timestamp_repair": "no manual date correction; row-order index only",
            "hourly_aggregation": "four consecutive quarter-hour powers; mean MW and energy MWh",
            "temperature_join": "HV timestamp_hour_end_utc equals DWD MESS_DATUM interpreted as UTC",
            "temperature_lags": "current hour and 1 to 7 previous UTC hours",
            "missing_temperature_imputation": False,
        },
        "coverage": {
            "rows": len(feature_rows),
            "complete_8lag_rows": sum(complete_by_year.values()),
            "excluded_8lag_rows": len(feature_rows) - sum(complete_by_year.values()),
            "features_path": str(features_path.relative_to(REPO)),
            "features_sha256": sha256(features_path),
            "audit_path": str(audit_path.relative_to(REPO)),
            "audit_sha256": sha256(audit_path),
        },
        "training_gate": {
            "recommended_split": {"train_years": [2020, 2021, 2022], "validation_years": [2023], "holdout_years": [2024]},
            "scaler_fit_policy": "training years only",
            "random_shuffle_policy": "no row redistribution across years; batch shuffle may occur only inside training partition",
            "sector_share_requirement": "year-specific annual shares for every training year; do not silently broadcast 2023 shares to 2020-2024",
            "next_step": "obtain/audit Strombilanz annual sector totals for 2020-2024, then build d=3/d=5/d=8 Parquet contracts",
        },
    }
    manifest_path = output_root / "berlin_multiyear_features_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    report_path = report_root / "berlin_multiyear_source_audit.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Auditoría de fuentes multianuales Berlín 2020-2024\n",
        "Esta entrega prepara la expansión temporal sin crear todavía un contrato de entrenamiento. La serie HV se normaliza a UTC y la temperatura DWD se une con rezagos causales de 0-7 horas.\n",
        "## Regla temporal\n",
        "Los CSV HV crudos se recorren en el orden publicado. Se genera el primer timestamp UTC a partir de 01-01 00:15 de Europe/Berlin y se incrementa cada 15 minutos. Esto evita corregir manualmente los errores de fecha 2020-2022, conserva todos los valores y registra las discrepancias frente a las etiquetas locales. La hora UTC es el índice canónico y no se elimina la hora repetida por DST.\n",
        "## Cobertura auditada\n",
        "",
        "| Año | Horas HV | Cuartos de hora | Desajustes de etiqueta | UTC continuo | Horas con 8 rezagos térmicos | Cobertura térmica | Energía calculada (GWh) | Comparación con fuente |",
        "|---:|---:|---:|---:|:---:|---:|---:|---:|---:|",
    ]
    for row in audit_rows:
        comparison = "" if row["computed_vs_declared_pct"] == "" else f"{row['computed_vs_declared_pct']} %"
        lines.append(
            f"| {row['year']} | {row['observed_hours']} | {row['observed_quarter_hour_rows']} | {row['timestamp_label_mismatch_count']} | {row['utc_contiguous']} | {row['complete_8lag_rows']} | {row['complete_8lag_pct']} % | {row['computed_energy_GWh']} | {comparison} |"
        )
    lines.extend([
        "",
        "## Dictamen de integración",
        "",
        "- La tabla horaria multianual queda disponible para auditoría; los valores HV no fueron imputados ni corregidos manualmente.",
        "- 2020-2022 deben considerarse años con riesgo temporal documentado hasta recibir confirmación del operador sobre las etiquetas DST.",
        "- El DWD histórico cubre los años solicitados; los faltantes se mantienen explícitos y las filas incompletas no se usarán en un contrato de entrenamiento.",
        "- La expansión aún no tiene GO para entrenar: faltan shares sectoriales anuales homologados para cada año. El siguiente control es auditar Strombilanz 2020-2024 y construir el contrato con entrenamiento 2020-2022, validación 2023 y holdout 2024.",
        "",
        f"Artefacto integrado: {features_path.relative_to(REPO)} (SHA-256 {sha256(features_path)}).",
        f"Manifiesto: {manifest_path.relative_to(REPO)}.",
    ])
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "features": str(features_path),
        "manifest": str(manifest_path),
        "audit": str(report_path),
        "rows": len(feature_rows),
        "complete_8lag_rows": sum(complete_by_year.values()),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
