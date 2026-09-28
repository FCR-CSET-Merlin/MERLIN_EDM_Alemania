"""Prepare comparable d=3, d=5 and d=8 temperature feature tables for Berlin."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[2]
UTC = timezone.utc
LOCAL_TZ = ZoneInfo("Europe/Berlin")
DIMENSIONS = (3, 5, 8)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_rows(demand: list[dict[str, str]], temperature: list[dict[str, str]], dimension: int) -> tuple[list[dict[str, object]], list[datetime]]:
    demand_by_time = {parse_utc(row["timestamp_hour_end_utc"]): row for row in demand}
    temp_by_time = {
        parse_utc(row["timestamp_utc"]): (None if row["temperature_C"] == "" else float(row["temperature_C"]))
        for row in temperature
    }
    rows: list[dict[str, object]] = []
    for timestamp in sorted(demand_by_time):
        values = [temp_by_time.get(timestamp - timedelta(hours=lag)) for lag in range(dimension)]
        if any(value is None for value in values):
            continue
        local = timestamp.astimezone(LOCAL_TZ)
        row: dict[str, object] = {
            "timestamp_hour_end_utc": timestamp.isoformat(),
            "timestamp_hour_end_local": local.isoformat(),
            "load_mean_MW": demand_by_time[timestamp]["load_mean_MW"],
            "energy_MWh": demand_by_time[timestamp]["energy_MWh"],
            "hour_local": local.hour,
            "day_of_week_local": local.weekday(),
            "month_local": local.month,
            "day_of_year_local": local.timetuple().tm_yday,
            "is_weekend_local": int(local.weekday() >= 5),
        }
        for lag, value in enumerate(values):
            row[f"temperature_t_minus_{lag}_C"] = f"{value:.1f}"
        rows.append(row)
    return rows, [parse_utc(row["timestamp_hour_end_utc"]) for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("demand", type=Path)
    parser.add_argument("temperature", type=Path)
    parser.add_argument("--output-root", type=Path, default=REPO / "prototipo_3/data/de_alemania/berlin_lag_ablation_2023")
    parser.add_argument("--report-index", type=Path, default=REPO / "corfo-report/validation/berlin/lag_ablation_2023_index.csv")
    args = parser.parse_args()
    demand_path = args.demand.resolve()
    temperature_path = args.temperature.resolve()
    demand = read_csv(demand_path)
    temperature = read_csv(temperature_path)
    if len(demand) != 8760 or len(temperature) != 8760:
        raise ValueError("The ablation requires 8760 demand and temperature rows")

    artifacts = []
    dimension_rows: dict[int, list[dict[str, object]]] = {}
    dimension_times: dict[int, set[datetime]] = {}
    fields_by_dim: dict[int, list[str]] = {}
    for dimension in DIMENSIONS:
        rows, times = build_rows(demand, temperature, dimension)
        fields = [
            "timestamp_hour_end_utc", "timestamp_hour_end_local", "load_mean_MW", "energy_MWh",
            *[f"temperature_t_minus_{lag}_C" for lag in range(dimension)],
            "hour_local", "day_of_week_local", "month_local", "day_of_year_local", "is_weekend_local",
        ]
        path = args.output_root / f"d{dimension}" / f"berlin_hv_temperature_d{dimension}_2023_complete.csv"
        write_csv(path, rows, fields)
        dimension_rows[dimension] = rows
        dimension_times[dimension] = set(times)
        fields_by_dim[dimension] = fields
        artifacts.append((f"d{dimension}", path, len(rows)))

    common_times = set.intersection(*(dimension_times[dimension] for dimension in DIMENSIONS))
    common_artifacts = []
    for dimension in DIMENSIONS:
        rows = [row for row in dimension_rows[dimension] if parse_utc(row["timestamp_hour_end_utc"]) in common_times]
        path = args.output_root / f"common_d3_d5_d8/d{dimension}" / f"berlin_hv_temperature_d{dimension}_2023_common.csv"
        write_csv(path, rows, fields_by_dim[dimension])
        common_artifacts.append((f"common_d{dimension}", path, len(rows)))

    all_artifacts = artifacts + common_artifacts
    report_rows = []
    for name, path, count in all_artifacts:
        report_rows.append({
            "dataset": name,
            "period": "2023",
            "rows": count,
            "frequency": "1h",
            "dimensions": name.rsplit("d", 1)[-1],
            "coverage_policy": "dimension-specific complete cases" if not name.startswith("common") else "common complete cases across d=3,d=5,d=8",
            "artifact": str(path.relative_to(REPO)),
            "artifact_sha256": sha256(path),
            "demand_input_sha256": sha256(demand_path),
            "temperature_input_sha256": sha256(temperature_path),
        })
    write_csv(args.report_index, report_rows, list(report_rows[0]))
    manifest = {
        "dataset": "berlin_lag_ablation_2023",
        "inputs": {"demand": str(demand_path), "demand_sha256": sha256(demand_path), "temperature": str(temperature_path), "temperature_sha256": sha256(temperature_path)},
        "dimensions": list(DIMENSIONS),
        "policy": "No imputation; each dimension uses complete temperature history; common set uses the intersection of valid timestamps.",
        "rows_by_dimension": {f"d{dimension}": len(dimension_rows[dimension]) for dimension in DIMENSIONS},
        "common_rows": len(common_times),
        "artifacts": [{"name": name, "path": str(path.relative_to(REPO)), "rows": count, "sha256": sha256(path)} for name, path, count in all_artifacts],
    }
    manifest_path = args.output_root / "berlin_lag_ablation_2023_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
