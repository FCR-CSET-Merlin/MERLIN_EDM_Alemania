"""Export row-level hourly inference for the trained Berlin d=3 model.

The script rebuilds the feature matrix from the auditable d=3 common table,
using the same calendar and scaling contract as the German training run. It
writes the complete rows available to that contract (not an imputed 8,760-hour
series) and records coverage, hashes and split metrics for reportability.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
UTC = timezone.utc
DEFAULT_MANIFEST = REPO / "prototipo_3/data/de_alemania/berlin_training_2023/berlin_training_contract_d3_2023_manifest.json"
DEFAULT_OUTPUT_ROOT = REPO / "prototipo_3/data/de_alemania/berlin_inference_2023"
REPORT_ROOT = REPO / "corfo-report/validation/berlin/inference_2023"


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
    timestamp = datetime.fromisoformat(value)
    if timestamp.tzinfo is None:
        raise ValueError(f"Timestamp without timezone: {value}")
    return timestamp.astimezone(UTC)


def load_contract_module():
    path = REPO / "prototipo_3/preprocessing/berlin_training_contract_2023.py"
    spec = importlib.util.spec_from_file_location("berlin_training_contract_2023", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import contract module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def metric(actual: list[float], predicted: list[float]) -> dict[str, float | int]:
    if not actual:
        return {"n": 0, "mape_pct": float("nan"), "mae_MW": float("nan"), "rmse_MW": float("nan"), "bias_MW": float("nan"), "actual_mean_MW": float("nan"), "predicted_mean_MW": float("nan")}
    errors = [p - a for a, p in zip(actual, predicted)]
    mape = sum(abs(e) / max(abs(a), 1e-9) for a, e in zip(actual, errors)) / len(actual) * 100.0
    mae = sum(abs(e) for e in errors) / len(errors)
    rmse = math.sqrt(sum(e * e for e in errors) / len(errors))
    return {
        "n": len(actual),
        "mape_pct": mape,
        "mae_MW": mae,
        "rmse_MW": rmse,
        "bias_MW": sum(errors) / len(errors),
        "actual_mean_MW": sum(actual) / len(actual),
        "predicted_mean_MW": sum(predicted) / len(predicted),
    }


def fmt(value: float | int | str) -> str:
    if isinstance(value, float):
        return f"{value:.9f}"
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-root", type=Path, default=REPORT_ROOT)
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if int(manifest.get("dimension")) != 3:
        raise ValueError("This exporter is restricted to the Berlin d=3 contract")
    input_path = (REPO / manifest["input"]["path"]).resolve()
    shares_path = (REPO / manifest["shares"]["path"]).resolve()
    weight_path = (REPO / "prototipo_3/data/de_alemania/berlin_training_2023/model_d3/best_merlin_mlp_berlin_d3.keras").resolve()
    for path in (input_path, shares_path, weight_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    rows = read_csv(input_path)
    if not rows:
        raise ValueError("The d=3 input table is empty")
    contract = load_contract_module()
    features = list(manifest["features"])
    expected_features = contract.feature_columns(3)
    if features != expected_features:
        raise ValueError(f"Feature order differs from contract: {features} != {expected_features}")
    required = {"timestamp_hour_end_utc", "timestamp_hour_end_local", "load_mean_MW", "energy_MWh", "temperature_t_minus_0_C", "temperature_t_minus_1_C", "temperature_t_minus_2_C"}
    missing = required.difference(rows[0])
    if missing:
        raise ValueError(f"Missing input columns: {sorted(missing)}")
    rows.sort(key=lambda row: parse_utc(row["timestamp_hour_end_utc"]))
    timestamps = [parse_utc(row["timestamp_hour_end_utc"]) for row in rows]
    if len(set(timestamps)) != len(timestamps):
        raise ValueError("Duplicate UTC timestamps")

    shares = read_csv(shares_path)
    if len(shares) != 1:
        raise ValueError("Expected one Berlin sector-share row")
    share = shares[0]
    temporal_resolution = manifest.get("shares", {}).get("temporal_resolution", manifest.get("sector_share_temporal_resolution", ""))
    if temporal_resolution != "annual_broadcast":
        raise ValueError(f"Expected annual_broadcast shares, got {temporal_resolution!r}")
    share_values = {name: float(share[name]) for name in ("region_comuna_share", "share_I", "share_R", "share_C", "share_P", "share_T")}
    mu = float(manifest["scaling"]["mu_train_MW"])
    sigma = float(manifest["scaling"]["sigma_train_MW"])
    split = manifest["split"]
    n_expected = int(split["train_rows"]) + int(split["validation_rows"]) + int(split["test_rows"])
    if len(rows) != n_expected:
        raise ValueError(f"Input rows {len(rows)} != contract split rows {n_expected}")

    matrix: list[list[float]] = []
    actual: list[float] = []
    for row, timestamp in zip(rows, timestamps):
        calendar = contract.build_calendar(timestamp)
        values: dict[str, float | int] = {**calendar, **share_values, "is_comuna": 0}
        values["temperatura"] = float(row["temperature_t_minus_0_C"])
        values["temp_t - 1"] = float(row["temperature_t_minus_1_C"])
        values["temp_t - 2"] = float(row["temperature_t_minus_2_C"])
        matrix.append([float(values[name]) for name in features])
        actual.append(float(row["load_mean_MW"]))
    import numpy as np
    import tensorflow as tf
    tf.keras.utils.set_random_seed(2023)
    model = tf.keras.models.load_model(weight_path, compile=False)
    predicted_scaled = model.predict(np.asarray(matrix, dtype=np.float32), batch_size=2048, verbose=0).reshape(-1).astype(float)
    predicted = (predicted_scaled * sigma + mu).tolist()
    if len(predicted) != len(rows):
        raise ValueError("Prediction length differs from input rows")

    train_end = int(split["train_rows"])
    validation_end = train_end + int(split["validation_rows"])
    split_names = (["train"] * train_end) + (["validation"] * (validation_end - train_end)) + (["test"] * (len(rows) - validation_end))
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    output_csv = output_root / "berlin_d3_inference_2023.csv"
    fields = ["timestamp_hour_end_utc", "timestamp_hour_end_local", "territory_code", "territory_name", "load_observed_MW", "load_predicted_MW", "energy_observed_MWh", "energy_predicted_MWh", "residual_MW", "residual_pct", "split", "coverage_flag", "model_dimension", "model_weight"]
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row, prediction, split_name in zip(rows, predicted, split_names):
            observed = float(row["load_mean_MW"])
            residual = prediction - observed
            writer.writerow({
                "timestamp_hour_end_utc": row["timestamp_hour_end_utc"],
                "timestamp_hour_end_local": row["timestamp_hour_end_local"],
                "territory_code": "11000",
                "territory_name": "Berlin",
                "load_observed_MW": fmt(observed),
                "load_predicted_MW": fmt(prediction),
                "energy_observed_MWh": fmt(float(row["energy_MWh"])),
                "energy_predicted_MWh": fmt(prediction),
                "residual_MW": fmt(residual),
                "residual_pct": fmt(residual / observed * 100.0 if observed else float("nan")),
                "split": split_name,
                "coverage_flag": "complete_d3_features",
                "model_dimension": 3,
                "model_weight": str(weight_path.relative_to(REPO)),
            })

    metrics = {}
    for name, lo, hi in (("all", 0, len(rows)), ("train", 0, train_end), ("validation", train_end, validation_end), ("test", validation_end, len(rows))):
        metrics[name] = metric(actual[lo:hi], predicted[lo:hi])
    observed_energy_gwh = sum(float(row["energy_MWh"]) for row in rows) / 1000.0
    predicted_energy_gwh = sum(predicted) / 1000.0
    expected_annual_hours = 8760
    coverage_pct = len(rows) / expected_annual_hours * 100.0
    inference_manifest = {
        "dataset": "berlin_d3_inference_2023",
        "status": "exported_row_level_inference",
        "dimension": 3,
        "tau_hours": int(manifest.get("tau_hours", 1)),
        "input": {"path": str(input_path.relative_to(REPO)), "sha256": sha256(input_path), "rows": len(rows), "expected_annual_hours": expected_annual_hours, "missing_hours": expected_annual_hours - len(rows), "coverage_pct": coverage_pct, "missing_policy": "not_imputed; only complete d=3 feature rows exported"},
        "contract_manifest": {"path": str(manifest_path.relative_to(REPO)), "sha256": sha256(manifest_path)},
        "shares": {"path": str(shares_path.relative_to(REPO)), "sha256": sha256(shares_path), "temporal_resolution": temporal_resolution},
        "model": {"path": str(weight_path.relative_to(REPO)), "sha256": sha256(weight_path), "feature_count": len(features), "features": features},
        "scaling": {"mu_train_MW": mu, "sigma_train_MW": sigma, "policy": "contract train partition"},
        "split": {"train_rows": train_end, "validation_rows": validation_end - train_end, "test_rows": len(rows) - validation_end, "policy": "chronological contract split"},
        "metrics": metrics,
        "annual_energy": {"observed_GWh_complete_rows": observed_energy_gwh, "predicted_GWh_complete_rows": predicted_energy_gwh, "basis": "8740 complete-feature rows; excludes 20 unavailable lag rows"},
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "tensorflow": tf.__version__},
        "output": {"path": str(output_csv.relative_to(REPO)), "sha256": sha256(output_csv), "rows": len(rows)},
    }
    manifest_output = output_root / "berlin_d3_inference_2023_manifest.json"
    manifest_output.write_text(json.dumps(inference_manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    inference_manifest["output"]["manifest_path"] = str(manifest_output.relative_to(REPO))
    inference_manifest["output"]["manifest_sha256"] = sha256(manifest_output)

    report_root = args.report_root.resolve()
    report_root.mkdir(parents=True, exist_ok=True)
    metrics_csv = report_root / "berlin_d3_inference_metrics_2023.csv"
    metric_fields = ["scope", "n", "mape_pct", "mae_MW", "rmse_MW", "bias_MW", "actual_mean_MW", "predicted_mean_MW"]
    with metrics_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=metric_fields, lineterminator="\n")
        writer.writeheader()
        for name in ("all", "train", "validation", "test"):
            writer.writerow({"scope": name, **{key: fmt(value) for key, value in metrics[name].items()}})
    summary = report_root / "berlin_d3_inference_2023_summary.md"
    summary.write_text(
        "# Inferencia horaria Berlín 2023 — contrato d=3\n\n"
        "La salida corresponde a la red MLP alemana d=3 entrenada con el contrato cronológico 2023. "
        "Se reconstruyen únicamente las horas con temperatura contemporánea y dos rezagos disponibles; no se imputan las 20 horas faltantes.\n\n"
        f"- Filas exportadas: **{len(rows)} de {expected_annual_hours}** ({coverage_pct:.6f} %).\n"
        f"- Cobertura: **{expected_annual_hours - len(rows)} horas no exportadas** por completitud de features d=3.\n"
        f"- Resolución temporal de shares sectoriales: **{temporal_resolution}**.\n"
        f"- Energía observada en filas completas: **{observed_energy_gwh:.6f} GWh**; predicha: **{predicted_energy_gwh:.6f} GWh**.\n"
        f"- MAPE test interno HV: **{metrics['test']['mape_pct']:.6f} %**; umbral operativo: **35 %**.\n"
        f"- MAE test: **{metrics['test']['mae_MW']:.6f} MW**; RMSE test: **{metrics['test']['rmse_MW']:.6f} MW**; sesgo test: **{metrics['test']['bias_MW']:.6f} MW**.\n\n"
        "## Alcance de validación\n\n"
        "La fila formal del KPI está en [`../kpi_validation.csv`](../kpi_validation.csv).\n\n"
        "El MAPE es una validación interna sobre el mismo perfil HV de Stromnetz Berlin utilizado como objetivo del entrenamiento y su partición temporal de test. "
        "Por tanto, acredita el desempeño de reconstrucción interna del piloto, pero no constituye todavía una validación horaria externa independiente.\n\n"
        "La tabla de filas y el manifiesto reproducible se mantienen en el área de datos ignorada; este resumen y la tabla de métricas son la evidencia reportable.\n",
        encoding="utf-8",
    )
    print(json.dumps({"output_csv": str(output_csv), "manifest": str(manifest_output), "metrics_csv": str(metrics_csv), "summary": str(summary), "metrics": metrics}, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
