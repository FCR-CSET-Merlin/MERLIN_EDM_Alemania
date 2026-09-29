"""Apply the provisional Berlin district allocation rule to d=3 inference.

Rule: for every complete hour, distribute the Berlin aggregate prediction using
fixed 2023 annual district shares from the Umweltatlas field ``j2023g``. This
is an operational disaggregation/calibration scenario; because the same annual
shares define the allocation, the district share comparison is not an
independent spatial validation of the neural network.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_INFERENCE = REPO / "prototipo_3/data/de_alemania/berlin_inference_2023/berlin_d3_inference_2023.csv"
DEFAULT_DISTRICTS = REPO / "corfo-report/validation/berlin/external_2023/berlin_umweltatlas_bezirke_2023.csv"
DEFAULT_OUTPUT_ROOT = REPO / "prototipo_3/data/de_alemania/berlin_district_inference_2023"
DEFAULT_REPORT_ROOT = REPO / "corfo-report/validation/berlin/inference_2023"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def f(value: float) -> str:
    return f"{value:.9f}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inference", type=Path, default=DEFAULT_INFERENCE)
    parser.add_argument("--districts", type=Path, default=DEFAULT_DISTRICTS)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    args = parser.parse_args()
    inference_path = args.inference.resolve()
    districts_path = args.districts.resolve()
    if not inference_path.is_file() or not districts_path.is_file():
        raise FileNotFoundError("Inference or district reference file is missing")
    inference = read_csv(inference_path)
    districts = read_csv(districts_path)
    if not inference or len(districts) != 12:
        raise ValueError(f"Expected non-empty inference and 12 districts, got {len(inference)}, {len(districts)}")
    annual_values = [float(row["j2023g_gwh"]) for row in districts]
    total_reference = sum(annual_values)
    if total_reference <= 0:
        raise ValueError("District reference total must be positive")
    weights = [value / total_reference for value in annual_values]
    if not math.isclose(sum(weights), 1.0, abs_tol=1e-12):
        raise ValueError("District weights do not sum to one")

    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    output_csv = output_root / "berlin_district_d3_inference_2023.csv"
    fields = ["timestamp_hour_end_utc", "timestamp_hour_end_local", "id_bezirk", "bezirk", "district_weight", "city_predicted_MW", "district_predicted_MW", "allocation_rule", "coverage_flag"]
    annual_predicted = [0.0] * len(districts)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in inference:
            city_prediction = float(row["load_predicted_MW"])
            for index, (district, weight) in enumerate(zip(districts, weights)):
                district_prediction = city_prediction * weight
                annual_predicted[index] += district_prediction
                writer.writerow({
                    "timestamp_hour_end_utc": row["timestamp_hour_end_utc"],
                    "timestamp_hour_end_local": row["timestamp_hour_end_local"],
                    "id_bezirk": district["id_bezirk"],
                    "bezirk": district["bezirk"],
                    "district_weight": f(weight),
                    "city_predicted_MW": f(city_prediction),
                    "district_predicted_MW": f(district_prediction),
                    "allocation_rule": "annual_umweltatlas_share_2023",
                    "coverage_flag": row.get("coverage_flag", "complete_d3_features"),
                })

    city_predicted_gwh = sum(float(row["load_predicted_MW"]) for row in inference) / 1000.0
    annual_rows: list[dict[str, str | float]] = []
    share_errors: list[float] = []
    for index, (district, weight, prediction_mw) in enumerate(zip(districts, weights, annual_predicted)):
        predicted_gwh = prediction_mw / 1000.0
        reference_gwh = float(district["j2023g_gwh"])
        predicted_share = predicted_gwh / city_predicted_gwh if city_predicted_gwh else float("nan")
        share_error_pp = (predicted_share - weight) * 100.0
        share_errors.append(share_error_pp)
        annual_rows.append({
            "id_bezirk": district["id_bezirk"],
            "bezirk": district["bezirk"],
            "reference_j2023g_GWh": reference_gwh,
            "reference_share_pct": weight * 100.0,
            "predicted_district_GWh_complete_rows": predicted_gwh,
            "predicted_share_pct": predicted_share * 100.0,
            "share_error_pp": share_error_pp,
            "relative_error_pct": (predicted_gwh - reference_gwh) / reference_gwh * 100.0,
            "allocation_rule": "annual_umweltatlas_share_2023",
            "spatial_validation_status": "consistencia_condicionada_no_independiente",
        })

    report_root = args.report_root.resolve()
    report_root.mkdir(parents=True, exist_ok=True)
    annual_csv = report_root / "berlin_district_allocation_2023.csv"
    annual_fields = ["id_bezirk", "bezirk", "reference_j2023g_GWh", "reference_share_pct", "predicted_district_GWh_complete_rows", "predicted_share_pct", "share_error_pp", "relative_error_pct", "allocation_rule", "spatial_validation_status"]
    with annual_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=annual_fields)
        writer.writeheader()
        for row in annual_rows:
            writer.writerow({key: f(value) if isinstance(value, float) else value for key, value in row.items()})

    district_manifest = {
        "dataset": "berlin_district_d3_inference_2023",
        "status": "conditional_annual_share_allocation",
        "allocation_rule": "P_d,h = P_Berlin,h * (j2023g_d / sum_d j2023g_d)",
        "interpretation": "Fixed annual shares provide an operational district scenario; they do not create independent district hourly observations or an independent spatial KPI.",
        "inference": {"path": str(inference_path.relative_to(REPO)), "sha256": sha256(inference_path), "rows": len(inference)},
        "district_reference": {"path": str(districts_path.relative_to(REPO)), "sha256": sha256(districts_path), "districts": len(districts), "total_j2023g_GWh": total_reference},
        "weights_sum": sum(weights),
        "city_predicted_energy_GWh_complete_rows": city_predicted_gwh,
        "city_vs_reference_relative_error_pct": (city_predicted_gwh - total_reference) / total_reference * 100.0,
        "district_share_error_max_abs_pp": max(abs(error) for error in share_errors),
        "outputs": {"hourly_path": str(output_csv.relative_to(REPO)), "hourly_sha256": sha256(output_csv), "hourly_rows": len(inference) * len(districts), "annual_summary_path": str(annual_csv.relative_to(REPO)), "annual_summary_sha256": sha256(annual_csv)},
    }
    manifest_path = output_root / "berlin_district_d3_inference_2023_manifest.json"
    manifest_path.write_text(json.dumps(district_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary_path = report_root / "spatial_validation_berlin_d3_2023.md"
    summary_path.write_text(
        "# Capa espacial Berlín 2023 — inferencia d=3\n\n"
        "## Regla provisional de desagregación\n\n"
        "Para cada hora completa de la inferencia agregada se calcula `P_d,h = P_Berlin,h × w_d`, donde `w_d = j2023g_d / Σj2023g_d` y `j2023g` es el consumo anual 2023 por distrito publicado por Umweltatlas. La regla mantiene la forma horaria del agregado y asigna a cada distrito una participación anual fija.\n\n"
        f"- Distritos cubiertos: **{len(districts)}/12**.\n"
        f"- Total de referencia `j2023g`: **{total_reference:.6f} GWh**.\n"
        f"- Energía predicha Berlín en las filas completas: **{city_predicted_gwh:.6f} GWh**.\n"
        f"- Diferencia del total predicho frente a Umweltatlas: **{(city_predicted_gwh - total_reference) / total_reference * 100.0:.6f} %**.\n"
        f"- Error máximo de participación distrital: **{max(abs(error) for error in share_errors):.12f} puntos porcentuales**, por construcción.\n\n"
        "## Evaluación de la capa espacial\n\n"
        "El resultado distrital es **consistencia condicionada; no validación espacial independiente**. Las mismas participaciones `j2023g` de Umweltatlas que se usan como pesos definen la referencia de shares, por lo que una coincidencia de participaciones no demuestra que la red haya aprendido diferencias horarias entre distritos. La única discrepancia independiente disponible en esta etapa es el control del total agregado, afectado además por la cobertura de 8.740/8.760 horas y por la diferencia de perímetro entre HV y consumo distrital.\n\n"
        "Para declarar un KPI espacial independiente se requiere una serie horaria distrital externa o variables explicativas territorializadas (por ejemplo, cargas medidas por distrito, perfiles de clientes o un procedimiento de calibración con observaciones fuera de `j2023g`). Hasta entonces, esta regla sirve para producir un escenario distrital reproducible y para preparar la integración cartográfica.\n",
        encoding="utf-8",
    )
    print(json.dumps({"hourly_output": str(output_csv), "annual_summary": str(annual_csv), "manifest": str(manifest_path), "summary": str(summary_path), "city_predicted_GWh": city_predicted_gwh, "city_reference_GWh": total_reference, "city_relative_error_pct": (city_predicted_gwh - total_reference) / total_reference * 100.0, "max_share_error_pp": max(abs(error) for error in share_errors)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
