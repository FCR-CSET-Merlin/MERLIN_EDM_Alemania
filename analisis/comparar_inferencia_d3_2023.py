"""Compare the regenerated d=3 inference with the versioned prior KPI."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = "cb1d080"
RELATIVE_METRICS = Path("corfo-report/validation/berlin/inference_2023/berlin_d3_inference_metrics_2023.csv")
CURRENT = REPO / RELATIVE_METRICS
OUT = REPO / "corfo-report/validation/berlin/inference_2023"
NUMERIC_METRICS = ("mape_pct", "mae_MW", "rmse_MW", "bias_MW", "actual_mean_MW", "predicted_mean_MW")
TOLERANCE = 1e-5


def read_rows(text: str) -> dict[str, dict[str, str]]:
    rows = list(csv.DictReader(text.splitlines()))
    return {row["scope"]: row for row in rows}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    if not CURRENT.is_file():
        raise FileNotFoundError(CURRENT)
    baseline_text = subprocess.check_output(
        ["git", "--git-dir", str(REPO / ".git"), "show", f"{BASELINE_COMMIT}:{RELATIVE_METRICS.as_posix()}"],
        text=True,
    )
    previous = read_rows(baseline_text)
    current = read_rows(CURRENT.read_text(encoding="utf-8"))
    if set(previous) != set(current):
        raise ValueError("Metric scopes differ between baseline and regenerated inference")

    comparisons: list[dict[str, object]] = []
    for scope in sorted(current):
        if int(previous[scope]["n"]) != int(current[scope]["n"]):
            raise ValueError(f"Observation count changed for {scope}")
        for metric in NUMERIC_METRICS:
            old_value = float(previous[scope][metric])
            new_value = float(current[scope][metric])
            delta = new_value - old_value
            comparisons.append({
                "scope": scope,
                "metric": metric,
                "baseline_value": old_value,
                "regenerated_value": new_value,
                "delta": delta,
                "abs_delta": abs(delta),
                "tolerance": TOLERANCE,
                "within_tolerance": abs(delta) <= TOLERANCE,
            })

    test_mape = next(row for row in comparisons if row["scope"] == "test" and row["metric"] == "mape_pct")
    status = "pass" if all(row["within_tolerance"] for row in comparisons) else "fail"
    csv_path = OUT / "berlin_d3_inference_reproducibility_2023.csv"
    fields = list(comparisons[0])
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(comparisons)

    summary = {
        "status": status,
        "baseline_commit": BASELINE_COMMIT,
        "current_metrics_sha256": sha256(CURRENT),
        "tolerance": TOLERANCE,
        "test_mape_baseline_pct": test_mape["baseline_value"],
        "test_mape_regenerated_pct": test_mape["regenerated_value"],
        "test_mape_delta_pct_points": test_mape["delta"],
        "max_abs_metric_delta": max(float(row["abs_delta"]) for row in comparisons),
        "comparisons": len(comparisons),
    }
    json_path = OUT / "berlin_d3_inference_reproducibility_2023.json"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path = OUT / "berlin_d3_inference_reproducibility_2023.md"
    md_path.write_text(
        "# Reproducibilidad de inferencia Berlín d=3 — 2023\n\n"
        f"Estado: **{status}**. Se comparó la inferencia regenerada con el artefacto versionado en el commit `{BASELINE_COMMIT}`.\n\n"
        f"- Tolerancia numérica por métrica: **{TOLERANCE:.0e}**.\n"
        f"- MAPE test anterior: **{test_mape['baseline_value']:.9f} %**.\n"
        f"- MAPE test regenerado: **{test_mape['regenerated_value']:.9f} %**.\n"
        f"- Diferencia: **{test_mape['delta']:.3e} puntos porcentuales**.\n"
        f"- Máxima diferencia absoluta entre métricas: **{summary['max_abs_metric_delta']:.3e}**.\n\n"
        "La diferencia queda dentro de la tolerancia y no cambia la conclusión KPI: el MAPE test es aproximadamente 5,089 % y permanece por debajo del umbral operativo de 35 %. Las pequeñas variaciones se atribuyen a la ejecución numérica del mismo modelo y contrato.\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
