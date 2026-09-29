"""Run a frozen d=3 temporal holdout for Berlin 2024.

The model, scaler and 2023 sector shares are frozen. The script only prepares
2024 observations, builds causal temperature lags, predicts complete rows and
reports the result as temporal generalisation within the Stromnetz Berlin HV
series. It is not an independent-operator validation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import math
import platform
import sys
import zipfile
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[1]
UTC = timezone.utc
BERLIN = ZoneInfo("Europe/Berlin")
YEAR = 2024
EXPECTED_HV_QUARTERS = 366 * 96
EXPECTED_HOURS = 366 * 24
DEFAULT_HV = REPO / "prototipo_3/data/de_alemania/external_validation/berlin_2024/Jahreshoechstlast-2024-Hochspannung.csv"
DEFAULT_DWD = REPO / "prototipo_3/data/de_alemania/external_validation/berlin_2024/stundenwerte_TU_00433_hist.zip"
DEFAULT_CONTRACT = REPO / "prototipo_3/data/de_alemania/berlin_training_2023/berlin_training_contract_d3_2023_manifest.json"
DEFAULT_SHARES = REPO / "corfo-report/validation/berlin/berlin_sector_shares_2023.csv"
DEFAULT_MODEL = REPO / "prototipo_3/data/de_alemania/berlin_training_2023/model_d3/best_merlin_mlp_berlin_d3.keras"
DEFAULT_OUTPUT = REPO / "prototipo_3/data/de_alemania/berlin_temporal_validation_2024"
DEFAULT_REPORT = REPO / "corfo-report/validation/berlin/temporal_2024"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_hv_value(value: str) -> int:
    cleaned = value.strip().replace(".", "").replace(",", ".")
    return int(round(float(cleaned)))


def parse_hv(path: Path) -> list[dict[str, object]]:
    raw: list[tuple[int, str, int]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for source_row, row in enumerate(csv.reader(handle, delimiter=";"), start=1):
            if len(row) < 3:
                continue
            date_text, time_text, value = (cell.strip() for cell in row[:3])
            try:
                published = datetime.strptime(f"{date_text} {time_text}", "%d.%m.%Y %H:%M")
            except ValueError:
                continue
            raw.append((source_row, published.isoformat(sep=" "), parse_hv_value(value)))
    if len(raw) != EXPECTED_HV_QUARTERS:
        raise ValueError(f"Expected {EXPECTED_HV_QUARTERS} HV rows for {YEAR}, got {len(raw)}")
    first_local = datetime(YEAR, 1, 1, 0, 15, tzinfo=BERLIN)
    first_utc = first_local.astimezone(UTC)
    result: list[dict[str, object]] = []
    for position, (source_row, published, value_kw) in enumerate(raw):
        timestamp = first_utc + timedelta(minutes=15 * position)
        result.append({
            "source_row": source_row,
            "published_timestamp_local": published,
            "timestamp_utc": timestamp,
            "timestamp_local": timestamp.astimezone(BERLIN),
            "value_kw": value_kw,
            "label_mismatch": int(datetime.fromisoformat(published) != timestamp.astimezone(BERLIN).replace(tzinfo=None)),
        })
    for left, right in zip(result, result[1:]):
        if right["timestamp_utc"] - left["timestamp_utc"] != timedelta(minutes=15):
            raise ValueError("HV UTC sequence is not quarter-hourly")
    hourly: list[dict[str, object]] = []
    for start in range(0, len(result), 4):
        group = result[start:start + 4]
        last = group[-1]["timestamp_utc"]
        values = [int(row["value_kw"]) for row in group]
        hourly.append({
            "timestamp_hour_end_utc": last,
            "timestamp_hour_end_local": last.astimezone(BERLIN),
            "load_observed_MW": sum(values) / 4 / 1000.0,
            "energy_observed_MWh": sum(values) * 0.25 / 1000.0,
            "label_mismatch_count": sum(int(row["label_mismatch"]) for row in group),
        })
    if len(hourly) != EXPECTED_HOURS:
        raise ValueError(f"Expected {EXPECTED_HOURS} hourly HV rows, got {len(hourly)}")
    return hourly


def read_dwd(path: Path) -> tuple[dict[datetime, float | None], str]:
    with zipfile.ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.startswith("produkt_tu_stunde_") and name.endswith(".txt")]
        if len(members) != 1:
            raise ValueError(f"Expected one DWD temperature member, got {members}")
        member = members[0]
        with archive.open(member) as binary:
            text = io.TextIOWrapper(binary, encoding="latin-1")
            reader = csv.DictReader(text, delimiter=";")
            values: dict[datetime, float | None] = {}
            for row in reader:
                stamp_text = row["MESS_DATUM"].strip()
                if len(stamp_text) != 10 or not stamp_text.startswith(str(YEAR)):
                    continue
                timestamp = datetime.strptime(stamp_text, "%Y%m%d%H").replace(tzinfo=UTC)
                raw = row["TT_TU"].strip()
                values[timestamp] = None if raw in {"", "-999"} else float(raw)
    if len(values) != EXPECTED_HOURS:
        raise ValueError(f"Expected {EXPECTED_HOURS} DWD rows for {YEAR}, got {len(values)}")
    return values, member


def load_contract_module():
    path = REPO / "prototipo_3/preprocessing/berlin_training_contract_2023.py"
    spec = importlib.util.spec_from_file_location("berlin_training_contract_2023", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def metrics(actual: list[float], predicted: list[float]) -> dict[str, float | int]:
    errors = [p - a for a, p in zip(actual, predicted)]
    return {
        "n": len(actual),
        "mape_pct": sum(abs(e) / max(abs(a), 1e-9) for a, e in zip(actual, errors)) / len(actual) * 100.0,
        "mae_MW": sum(abs(e) for e in errors) / len(errors),
        "rmse_MW": math.sqrt(sum(e * e for e in errors) / len(errors)),
        "bias_MW": sum(errors) / len(errors),
        "actual_mean_MW": sum(actual) / len(actual),
        "predicted_mean_MW": sum(predicted) / len(predicted),
    }


def fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.9f}"
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hv", type=Path, default=DEFAULT_HV)
    parser.add_argument("--dwd", type=Path, default=DEFAULT_DWD)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--shares", type=Path, default=DEFAULT_SHARES)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    paths = {name: value.resolve() for name, value in vars(args).items() if isinstance(value, Path)}
    for name, path in paths.items():
        if name not in {"output_root", "report_root"} and not path.is_file():
            raise FileNotFoundError(f"{name}: {path}")

    contract_manifest = json.loads(paths["contract"].read_text(encoding="utf-8"))
    if contract_manifest.get("dimension") != 3:
        raise ValueError("The frozen temporal validation requires d=3")
    features = list(contract_manifest["features"])
    contract = load_contract_module()
    if features != contract.feature_columns(3):
        raise ValueError("Frozen feature order does not match the training contract")
    share_rows = read_csv(paths["shares"])
    if len(share_rows) != 1:
        raise ValueError("Expected one frozen 2023 sector-share row")
    share = share_rows[0]
    shares = {name: float(share[name]) for name in ("region_comuna_share", "share_I", "share_R", "share_C", "share_P", "share_T")}
    mu = float(contract_manifest["scaling"]["mu_train_MW"])
    sigma = float(contract_manifest["scaling"]["sigma_train_MW"])

    hv = parse_hv(paths["hv"])
    temperatures, dwd_member = read_dwd(paths["dwd"])
    complete: list[tuple[dict[str, object], datetime, list[float]]] = []
    missing_rows = 0
    for row in hv:
        timestamp = row["timestamp_hour_end_utc"]
        lag_values = [temperatures.get(timestamp - timedelta(hours=lag)) for lag in range(3)]
        if any(value is None for value in lag_values):
            missing_rows += 1
            continue
        complete.append((row, timestamp, [float(value) for value in lag_values]))
    if not complete:
        raise ValueError("No complete 2024 feature rows")

    matrix: list[list[float]] = []
    actual: list[float] = []
    for row, timestamp, lag_values in complete:
        values: dict[str, float | int] = {**contract.build_calendar(timestamp), **shares, "is_comuna": 0, "temperatura": lag_values[0], "temp_t - 1": lag_values[1], "temp_t - 2": lag_values[2]}
        matrix.append([float(values[name]) for name in features])
        actual.append(float(row["load_observed_MW"]))

    import numpy as np
    import tensorflow as tf
    tf.keras.utils.set_random_seed(2023)
    model = tf.keras.models.load_model(paths["model"], compile=False)
    predicted_scaled = model.predict(np.asarray(matrix, dtype=np.float32), batch_size=2048, verbose=0).reshape(-1).astype(float)
    predicted = (predicted_scaled * sigma + mu).tolist()
    all_metrics = metrics(actual, predicted)

    output_root = paths["output_root"]
    output_root.mkdir(parents=True, exist_ok=True)
    output_csv = output_root / "berlin_d3_temporal_validation_2024.csv"
    fields = ["timestamp_hour_end_utc", "timestamp_hour_end_local", "territory_code", "territory_name", "load_observed_MW", "load_predicted_MW", "energy_observed_MWh", "energy_predicted_MWh", "residual_MW", "residual_pct", "coverage_flag", "validation_scope", "model_dimension", "model_weight"]
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row, prediction in zip((item[0] for item in complete), predicted):
            observed = float(row["load_observed_MW"])
            residual = prediction - observed
            writer.writerow({
                "timestamp_hour_end_utc": row["timestamp_hour_end_utc"].isoformat(),
                "timestamp_hour_end_local": row["timestamp_hour_end_local"].isoformat(),
                "territory_code": "11000",
                "territory_name": "Berlin",
                "load_observed_MW": fmt(observed),
                "load_predicted_MW": fmt(prediction),
                "energy_observed_MWh": fmt(float(row["energy_observed_MWh"])),
                "energy_predicted_MWh": fmt(prediction),
                "residual_MW": fmt(residual),
                "residual_pct": fmt(residual / observed * 100.0 if observed else float("nan")),
                "coverage_flag": "complete_d3_features",
                "validation_scope": "temporal_holdout_2024_same_operator",
                "model_dimension": 3,
                "model_weight": str(paths["model"].relative_to(REPO)),
            })

    peak_actual_index = max(range(len(actual)), key=actual.__getitem__)
    peak_pred_index = max(range(len(predicted)), key=predicted.__getitem__)
    local_labels = [timestamp.astimezone(BERLIN).replace(tzinfo=None) for _, timestamp, _ in complete]
    duplicates = sum(count - 1 for count in Counter(local_labels).values() if count > 1)
    coverage_pct = len(complete) / EXPECTED_HOURS * 100.0
    observed_energy_gwh = sum(actual) / 1000.0
    predicted_energy_gwh = sum(predicted) / 1000.0
    manifest = {
        "dataset": "berlin_d3_temporal_validation_2024",
        "status": "frozen_model_temporal_holdout",
        "validation_scope": "temporal_generalisation_same_operator; not independent_source_validation",
        "year": YEAR,
        "model": {"path": str(paths["model"].relative_to(REPO)), "sha256": sha256(paths["model"]), "dimension": 3, "features": features},
        "contract_2023": {"path": str(paths["contract"].relative_to(REPO)), "sha256": sha256(paths["contract"]), "mu_train_MW": mu, "sigma_train_MW": sigma, "shares_year": int(share["year"])},
        "inputs": {
            "hv": {"path": str(paths["hv"].relative_to(REPO)), "sha256": sha256(paths["hv"]), "quarter_hour_rows": EXPECTED_HV_QUARTERS, "hour_rows": EXPECTED_HOURS, "label_mismatch_count": sum(int(row["label_mismatch_count"]) for row in hv)},
            "dwd": {"path": str(paths["dwd"].relative_to(REPO)), "sha256": sha256(paths["dwd"]), "member": dwd_member, "rows": EXPECTED_HOURS, "missing_temperature_rows": sum(value is None for value in temperatures.values())},
        },
        "coverage": {"expected_hours": EXPECTED_HOURS, "valid_feature_hours": len(complete), "missing_feature_hours": missing_rows, "coverage_pct": coverage_pct, "missing_policy": "no imputation; complete d=3 rows only"},
        "metrics": {"temporal_2024": all_metrics},
        "energy": {"observed_complete_rows_GWh": observed_energy_gwh, "predicted_complete_rows_GWh": predicted_energy_gwh, "basis": "complete feature rows only"},
        "peaks": {"actual_max_MW": max(actual), "actual_max_timestamp_utc": complete[peak_actual_index][1].isoformat(), "predicted_max_MW": max(predicted), "predicted_max_timestamp_utc": complete[peak_pred_index][1].isoformat(), "peak_error_pct": (max(predicted) - max(actual)) / max(actual) * 100.0},
        "dst": {"timezone": "Europe/Berlin", "duplicate_local_hour_labels": duplicates, "canonical_index": "UTC"},
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "tensorflow": tf.__version__},
    }
    manifest["output"] = {"path": str(output_csv.relative_to(REPO)), "sha256": sha256(output_csv), "rows": len(complete)}
    manifest_path = output_root / "berlin_d3_temporal_validation_2024_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    report_root = paths["report_root"]
    report_root.mkdir(parents=True, exist_ok=True)
    metrics_csv = report_root / "berlin_d3_temporal_validation_2024_metrics.csv"
    with metrics_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["scope", "year", "n", "coverage_pct", "mape_pct", "mae_MW", "rmse_MW", "bias_MW", "actual_mean_MW", "predicted_mean_MW", "observed_complete_GWh", "predicted_complete_GWh", "peak_error_pct", "duplicate_local_hour_labels"] , lineterminator="\n")
        writer.writeheader()
        writer.writerow({"scope": "temporal_holdout_2024_same_operator", "year": YEAR, "n": len(complete), "coverage_pct": fmt(coverage_pct), **{key: fmt(value) for key, value in all_metrics.items()}, "observed_complete_GWh": fmt(observed_energy_gwh), "predicted_complete_GWh": fmt(predicted_energy_gwh), "peak_error_pct": fmt(manifest["peaks"]["peak_error_pct"]), "duplicate_local_hour_labels": duplicates})

    summary = report_root / "berlin_d3_temporal_validation_2024_summary.md"
    summary.write_text(
        "# Validación temporal Berlín 2024 — modelo d=3 congelado\n\n"
        "Se aplicó sin reentrenamiento el modelo d=3 ajustado con 2023. Se conservaron la arquitectura, las 19 variables, el scaler y los shares sectoriales 2023. El resultado mide generalización temporal dentro de la serie HV del mismo operador; no es validación independiente de fuente.\n\n"
        f"- Cobertura: **{len(complete)}/{EXPECTED_HOURS} horas** ({coverage_pct:.6f} %); horas no imputadas: **{missing_rows}**.\n"
        f"- MAPE: **{all_metrics['mape_pct']:.6f} %**.\n"
        f"- MAE: **{all_metrics['mae_MW']:.6f} MW**; RMSE: **{all_metrics['rmse_MW']:.6f} MW**; sesgo: **{all_metrics['bias_MW']:.6f} MW**.\n"
        f"- Energía observada en filas completas: **{observed_energy_gwh:.6f} GWh**; predicha: **{predicted_energy_gwh:.6f} GWh**.\n"
        f"- Error de punta: **{manifest['peaks']['peak_error_pct']:.6f} %**.\n"
        f"- Etiquetas de hora local duplicadas por DST: **{duplicates}**; índice canónico: UTC.\n\n"
        "## Interpretación para KPI\n\n"
        "Este resultado puede reportarse como validación fuera de muestra temporal (`comparador_independiente=no`, `dependencia_input=si` respecto del operador y de la familia HV). No debe presentarse como una validación externa independiente de Berlín. La validación de fuente independiente queda `no_evaluable` mientras no exista una serie horaria medida con perímetro compatible y procedencia distinta.\n",
        encoding="utf-8",
    )
    print(json.dumps({"metrics": all_metrics, "coverage_pct": coverage_pct, "missing_rows": missing_rows, "output": str(output_csv), "summary": str(summary)}, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
