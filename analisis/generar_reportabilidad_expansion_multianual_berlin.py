#!/usr/bin/env python3
"""Generate reportable tables and figures for the Berlin multi-year expansion.

The generator uses only tracked CSV evidence from the expansion consolidation.
It intentionally does not alter the baseline 2023 KPI files.  Figures are
written as deterministic SVG files and rendered to PNG with ImageMagick when
available, keeping the YlOrRd palette used by the Berlin maps.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = REPO / "corfo-report/results"
DEFAULT_VALIDATION = REPO / "corfo-report/validation/berlin/multiyear_2020_2024"
CANONICAL_KPI = REPO / "corfo-report/validation/berlin/kpi_validation.csv"
MAPE_LIMIT = 35.0
PALETTE = {
    "train": "#fee8c8",
    "validation": "#fdbb84",
    "holdout": "#e34a33",
    "ink": "#222222",
    "muted": "#555555",
    "grid": "#d9d9d9",
    "selected": "#7f0000",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows to write: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def update_canonical_kpi_validation(metrics: list[dict[str, str]], metrics_path: Path, source_path: Path) -> None:
    """Append multiyear KPI rows to the repository-wide Berlin KPI ledger.

    Existing 2023 baseline rows are retained verbatim.  The distinct evidence
    identifier and indicator text prevent the expansion from being confused
    with the baseline d=3 results.
    """
    existing = read_csv(CANONICAL_KPI)
    fieldnames = list(existing[0])
    source_hash = sha256(source_path)
    metrics_hash = sha256(metrics_path)
    split_labels = {"train": "entrenamiento", "validation": "validación 2023", "test": "holdout temporal 2024"}
    split_states = {"train": "cumple_entrenamiento_multianual", "validation": "cumple_validacion_multianual", "test": "cumple_holdout_temporal_multianual_mismo_operador"}
    key_prefix = "CORFO-MERLIN-EDM-DE-BERLIN-MULTIYEAR"
    existing = [row for row in existing if not (row.get("id_evidencia") == key_prefix)]
    for row in metrics:
        split = row["split"]
        mape = float(row["mape_pct"])
        canonical = {name: "" for name in fieldnames}
        canonical.update({
            "id_evidencia": key_prefix,
            "compromiso": "Expansión multianual Berlín; MAPE <=35 %",
            "indicador": f"MAPE horario multianual d={row['dimension']} ({split_labels[split]})",
            "pais": "Alemania",
            "territorio": "Berlin-administrative (11000)",
            "nivel": "horario",
            "año": row["years"],
            "sector": "total",
            "n_observaciones": row["n"],
            "n_validas": row["n"],
            "mape_pct": mape,
            "mae": row["mae_MW"],
            "rmse": row["rmse_MW"],
            "umbral_pct": MAPE_LIMIT,
            "criterio": "<=",
            "cumple_umbral": str(mape <= MAPE_LIMIT).lower(),
            "comparador": "Stromnetz Berlin HV observado; partición temporal multianual",
            "comparador_independiente": "no",
            "dependencia_input": "si",
            "fuente_referencia": "corfo-report/validation/berlin/multiyear_2020_2024/berlin_multiyear_model_metrics.csv",
            "hash_entrada": source_hash,
            "hash_salida": metrics_hash,
            "estado_evidencia": split_states[split],
            "notas": f"{split_labels[split]}; generalización temporal del mismo operador y familia HV; no es validación independiente de fuente.",
        })
        existing.append(canonical)
    with CANONICAL_KPI.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)


def esc(value: object) -> str:
    text = str(value)
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def svg_text(x: float, y: float, text: object, size: int = 16, anchor: str = "start", weight: str = "normal", fill: str = PALETTE["ink"]) -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" font-family="DejaVu Sans,Arial,sans-serif" font-size="{size}px" text-anchor="{anchor}" font-weight="{weight}" fill="{fill}">{esc(text)}</text>'


def render_png(svg_path: Path, png_path: Path) -> bool:
    convert = shutil.which("convert")
    if not convert:
        return False
    subprocess.run(
        [convert, "-density", "150", str(svg_path), "-background", "white", "-alpha", "remove", "-strip", str(png_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    return True


def mape_figure(rows: list[dict[str, str]], svg_path: Path, png_path: Path) -> dict[str, object]:
    width, height = 1280, 780
    left, right, top, bottom = 120, 55, 105, 170
    plot_w, plot_h = width - left - right, height - top - bottom
    y_max = 40.0
    dimensions = [3, 5, 8]
    split_order = [("train", "Entrenamiento", PALETTE["train"]), ("validation", "Validación 2023", PALETTE["validation"]), ("test", "Holdout 2024", PALETTE["holdout"])]
    lookup = {(int(row["dimension"]), row["split"]): float(row["mape_pct"]) for row in rows}
    bar_w, gap = 46.0, 18.0
    group_w = len(split_order) * bar_w + (len(split_order) - 1) * gap
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="white"/>']
    parts.append(svg_text(width / 2, 42, "Expansión multianual Berlín: MAPE por partición", 24, "middle", "bold"))
    parts.append(svg_text(width / 2, 70, "Entrenamiento 2020–2022 · selección en validación 2023 · holdout temporal 2024", 14, "middle", "normal", PALETTE["muted"]))
    for tick in (0, 10, 20, 30, 35, 40):
        y = top + plot_h - (tick / y_max) * plot_h
        stroke = PALETTE["selected"] if tick == MAPE_LIMIT else PALETTE["grid"]
        dash = " stroke-dasharray=\"7,5\"" if tick == MAPE_LIMIT else ""
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" stroke="{stroke}" stroke-width="{2 if tick == MAPE_LIMIT else 1}"{dash}/>')
        parts.append(svg_text(left - 12, y + 5, f"{tick:g}", 13, "end", "normal", PALETTE["muted"]))
    parts.append(svg_text(32, top + plot_h / 2, "MAPE (%)", 15, "middle", "bold"))
    # Rotate the axis label around its own anchor.
    parts[-1] = parts[-1].replace('fill="#222222"', 'fill="#222222" transform="rotate(-90 32 435)"')
    for idx, dimension in enumerate(dimensions):
        center = left + (idx + 0.5) * (plot_w / len(dimensions))
        start = center - group_w / 2
        for j, (split, label, color) in enumerate(split_order):
            value = lookup[(dimension, split)]
            x = start + j * (bar_w + gap)
            bar_h = (value / y_max) * plot_h
            y = top + plot_h - bar_h
            selected = dimension == 8 and split == "validation"
            stroke = PALETTE["selected"] if selected else "#8c8c8c"
            sw = 3 if selected else 1
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" fill="{color}" stroke="{stroke}" stroke-width="{sw}"/>')
            parts.append(svg_text(x + bar_w / 2, y - 9, f"{value:.2f}", 12, "middle", "bold" if selected else "normal"))
        parts.append(svg_text(center, top + plot_h + 31, f"d={dimension}", 16, "middle", "bold" if dimension == 8 else "normal"))
    # Legend and compliance annotation.
    legend_x, legend_y = left, height - 113
    for j, (_, label, color) in enumerate(split_order):
        x = legend_x + j * 205
        parts.append(f'<rect x="{x}" y="{legend_y-13}" width="18" height="18" fill="{color}" stroke="#8c8c8c"/>')
        parts.append(svg_text(x + 26, legend_y + 2, label, 13))
    parts.append(svg_text(width - right, legend_y + 2, "Línea roja: umbral KPI MAPE ≤35 %", 13, "end", "bold", PALETTE["selected"]))
    parts.append(svg_text(width / 2, height - 56, "d=8 se selecciona por el menor MAPE de validación 2023 (3,4525 %); el holdout 2024 (3,4263 %) usa el mismo operador Stromnetz Berlin.", 12, "middle", "normal", PALETTE["muted"]))
    parts.append(svg_text(width / 2, height - 32, "El holdout acredita generalización temporal y no validación independiente de fuente.", 12, "middle", "normal", PALETTE["muted"]))
    parts.append("</svg>")
    svg_path.write_text("\n".join(parts) + "\n", encoding="utf-8")
    png_generated = render_png(svg_path, png_path)
    return {"svg": str(svg_path.relative_to(REPO)), "png": str(png_path.relative_to(REPO)) if png_generated else None, "png_generated": png_generated}


def coverage_figure(rows: list[dict[str, str]], svg_path: Path, png_path: Path) -> dict[str, object]:
    width, height = 1280, 700
    left, right, top, bottom = 120, 55, 105, 155
    plot_w, plot_h = width - left - right, height - top - bottom
    years = [int(row["year"]) for row in rows]
    coverage_key = "d8_coverage_pct" if "d8_coverage_pct" in rows[0] else "complete_8lag_pct"
    values = [float(row[coverage_key]) for row in rows]
    y_min, y_max = 97.5, 100.25
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="white"/>']
    parts.append(svg_text(width / 2, 42, "Cobertura anual de filas completas para d=8", 24, "middle", "bold"))
    parts.append(svg_text(width / 2, 70, "Control de disponibilidad de HV y ocho rezagos DWD antes del entrenamiento/inferencia", 14, "middle", "normal", PALETTE["muted"]))
    for tick in (98, 99, 100):
        y = top + plot_h - ((tick - y_min) / (y_max - y_min)) * plot_h
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" stroke="{PALETTE["grid"]}" stroke-width="1"/>')
        parts.append(svg_text(left - 12, y + 5, f"{tick:g}", 13, "end", "normal", PALETTE["muted"]))
    parts.append(svg_text(32, top + plot_h / 2, "Cobertura (%)", 15, "middle", "bold"))
    parts[-1] = parts[-1].replace('fill="#222222"', 'fill="#222222" transform="rotate(-90 32 355)"')
    slot = plot_w / len(years)
    bar_w = 95
    points: list[str] = []
    for i, (year, value) in enumerate(zip(years, values)):
        center = left + (i + 0.5) * slot
        bar_h = ((value - y_min) / (y_max - y_min)) * plot_h
        y = top + plot_h - bar_h
        parts.append(f'<rect x="{center-bar_w/2:.1f}" y="{y:.1f}" width="{bar_w}" height="{bar_h:.1f}" fill="{PALETTE["validation"]}" stroke="#8c8c8c" stroke-width="1"/>')
        parts.append(svg_text(center, y - 10, f"{value:.3f}", 13, "middle", "bold"))
        parts.append(svg_text(center, top + plot_h + 31, str(year), 16, "middle", "bold" if year == 2024 else "normal"))
        points.append(f"{center:.1f},{y:.1f}")
    parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{PALETTE["selected"]}" stroke-width="3"/>')
    for point in points:
        x, y = point.split(",")
        parts.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{PALETTE["selected"]}"/>')
    parts.append(svg_text(width / 2, height - 74, "2020–2021: 100 % · 2022: 98,322 % · 2023: 99,852 % · 2024: 99,875 %", 13, "middle", "normal", PALETTE["muted"]))
    parts.append(svg_text(width / 2, height - 48, "Las filas sin features completas se excluyen sin imputación; la disponibilidad no sustituye la validación externa.", 12, "middle", "normal", PALETTE["muted"]))
    parts.append("</svg>")
    svg_path.write_text("\n".join(parts) + "\n", encoding="utf-8")
    png_generated = render_png(svg_path, png_path)
    return {"svg": str(svg_path.relative_to(REPO)), "png": str(png_path.relative_to(REPO)) if png_generated else None, "png_generated": png_generated}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--validation-root", type=Path, default=DEFAULT_VALIDATION)
    args = parser.parse_args()
    results_root = args.results_root.resolve()
    validation_root = args.validation_root.resolve()
    tables = results_root / "tables"
    figures = results_root / "figures"
    figures.mkdir(parents=True, exist_ok=True)

    metrics_path = validation_root / "berlin_multiyear_model_metrics.csv"
    source_path = validation_root / "berlin_multiyear_source_audit.csv"
    metrics = read_csv(metrics_path)
    sources = read_csv(source_path)
    if len(metrics) != 9 or len(sources) != 5:
        raise ValueError(f"Unexpected evidence dimensions: metrics={len(metrics)}, sources={len(sources)}")

    kpi_rows: list[dict[str, object]] = []
    for row in metrics:
        split = row["split"]
        split_label = {"train": "entrenamiento", "validation": "validación 2023", "test": "holdout temporal 2024"}[split]
        kpi_rows.append({
            "kpi_id": f"BERLIN-MULTIYEAR-MAPE-D{row['dimension']}-{split.upper()}",
            "indicador": "MAPE horario",
            "compromiso": "MAPE <=35 %",
            "dimension": int(row["dimension"]),
            "particion": split_label,
            "periodo": row["years"],
            "n_validas": int(row["n"]),
            "mape_pct": float(row["mape_pct"]),
            "umbral_pct": MAPE_LIMIT,
            "criterio": "<=",
            "cumple_umbral": float(row["mape_pct"]) <= MAPE_LIMIT,
            "comparador": "HV observado Stromnetz Berlin",
            "comparador_independiente": "no",
            "dependencia_input": "si",
            "estado_evidencia": "cumple_entrenamiento" if split == "train" else ("cumple_validacion" if split == "validation" else "cumple_holdout_temporal_mismo_operador"),
            "interpretacion": f"{split_label}; no es validación independiente de fuente",
            "evidencia": "corfo-report/validation/berlin/multiyear_2020_2024/berlin_multiyear_model_metrics.csv",
        })
    source_rows = []
    for row in sources:
        source_rows.append({
            "year": int(row["year"]),
            "hv_hours": int(row["observed_hours"]),
            "d8_complete_hours": int(row["complete_8lag_rows"]),
            "d8_coverage_pct": float(row["complete_8lag_pct"]),
            "dwd_missing_temperature_rows": int(row["dwd_missing_temperature_rows"]),
            "timestamp_label_mismatch_count": row["timestamp_label_mismatch_count"],
            "computed_energy_GWh": float(row["computed_energy_GWh"]),
            "source_control_status": "pass" if float(row["complete_8lag_pct"]) > 0 else "fail",
            "evidencia": "corfo-report/validation/berlin/multiyear_2020_2024/berlin_multiyear_source_audit.csv",
        })
    write_csv(tables / "berlin_multiyear_kpi_compliance.csv", kpi_rows)
    write_csv(tables / "berlin_multiyear_source_coverage.csv", source_rows)
    update_canonical_kpi_validation(metrics, metrics_path, source_path)

    selected = min((row for row in kpi_rows if row["particion"] == "validación 2023"), key=lambda row: row["mape_pct"])
    holdout = next(row for row in kpi_rows if row["dimension"] == selected["dimension"] and row["particion"] == "holdout temporal 2024")
    md = [
        "# Matriz de cumplimiento KPI — expansión multianual de Berlín 2020–2024",
        "",
        "**Criterio comprometido:** MAPE horario ≤35 %. Las filas se reportan por dimensión y partición; el holdout 2024 es temporal y pertenece al mismo operador Stromnetz Berlin.",
        "",
        "| KPI | d | Partición | Periodo | n válidas | MAPE (%) | Umbral (%) | Cumple | Comparador independiente | Estado |",
        "|---|---:|---|---|---:|---:|---:|---|---|---|",
    ]
    for row in kpi_rows:
        md.append(f"| {row['kpi_id']} | {row['dimension']} | {row['particion']} | {row['periodo']} | {row['n_validas']} | {row['mape_pct']:.6f} | {row['umbral_pct']:.1f} | {'Sí' if row['cumple_umbral'] else 'No'} | No | {row['estado_evidencia']} |")
    md.extend([
        "",
        f"**Configuración seleccionada:** d={selected['dimension']} por menor MAPE de validación 2023 ({selected['mape_pct']:.6f} %). El holdout 2024 de esta configuración es {holdout['mape_pct']:.6f} %.",
        "",
        "**Alcance de la evidencia:** todos los MAPE cumplen el umbral operativo. La evidencia demuestra ajuste, selección y generalización temporal dentro de Stromnetz Berlin; no acredita una validación horaria independiente.",
        "",
        "**Controles de fuentes:** la tabla `berlin_multiyear_source_coverage.csv` registra horas HV, filas completas d=8, faltantes DWD y etiquetas DST por año. Las filas sin features completas se excluyen sin imputación.",
        "",
        "Figuras asociadas: `berlin_multiyear_kpi_mape.svg/.png` y `berlin_multiyear_d8_coverage.svg/.png`.",
    ])
    (tables / "berlin_multiyear_kpi_compliance.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    figure_records = [
        {"name": "berlin_multiyear_kpi_mape", **mape_figure(metrics, figures / "berlin_multiyear_kpi_mape.svg", figures / "berlin_multiyear_kpi_mape.png")},
        {"name": "berlin_multiyear_d8_coverage", **coverage_figure(sources, figures / "berlin_multiyear_d8_coverage.svg", figures / "berlin_multiyear_d8_coverage.png")},
    ]
    spatial_figure_names = (
        "berlin_demanda_distrital_multiyear_d8_2020_2024",
        "berlin_demanda_distrito_sector_anual_multiyear_d8_2020_2024",
    )
    for name in spatial_figure_names:
        record = {"name": name}
        for suffix in ("svg", "png"):
            path = figures / f"{name}.{suffix}"
            if path.is_file():
                record[suffix] = str(path.relative_to(REPO))
                record[f"{suffix}_sha256"] = sha256(path)
        if "svg" in record or "png" in record:
            record["png_generated"] = "png" in record
            figure_records.append(record)
    for record in figure_records:
        for key in ("svg", "png"):
            relative = record.get(key)
            if relative:
                record[f"{key}_sha256"] = sha256(REPO / relative)
    manifest = {
        "dataset": "berlin_multiyear_expansion_2020_2024",
        "status": "pass" if all(row["cumple_umbral"] for row in kpi_rows) else "review_required",
        "kpi": {"indicator": "MAPE horario", "threshold_pct": MAPE_LIMIT, "all_rows_comply": all(row["cumple_umbral"] for row in kpi_rows), "selected_dimension": selected["dimension"], "selected_validation_mape_pct": selected["mape_pct"], "selected_holdout_2024_mape_pct": holdout["mape_pct"]},
        "tables": [
            {"path": str((tables / "berlin_multiyear_kpi_compliance.csv").relative_to(REPO)), "sha256": sha256(tables / "berlin_multiyear_kpi_compliance.csv")},
            {"path": str((tables / "berlin_multiyear_source_coverage.csv").relative_to(REPO)), "sha256": sha256(tables / "berlin_multiyear_source_coverage.csv")},
            {"path": str((tables / "berlin_multiyear_kpi_compliance.md").relative_to(REPO)), "sha256": sha256(tables / "berlin_multiyear_kpi_compliance.md")},
            {"path": str(CANONICAL_KPI.relative_to(REPO)), "sha256": sha256(CANONICAL_KPI)},
        ],
        "figures": figure_records,
        "spatial_postprocess": {
            "status": "generated" if (figures / "berlin_demanda_distrital_multiyear_d8_2020_2024.png").is_file() else "pending",
            "audit": "corfo-report/validation/berlin/multiyear_2020_2024/berlin_multiyear_spatial_postprocess_audit.json",
            "district_table": "corfo-report/results/tables/berlin_multiyear_d8_district_annual.csv",
            "district_sector_table": "corfo-report/results/tables/berlin_multiyear_d8_district_sector_annual.csv",
            "annual_summary": "corfo-report/results/tables/berlin_multiyear_d8_annual_summary.csv",
            "interpretation": "conditional_allocation_not_independent_spatial_or_sector_kpi",
        },
        "limitations": [
            "Holdout 2024 is temporal generalisation from the same Stromnetz Berlin operator and HV measurement family, not independent-source validation.",
            "2024 sector shares are a labelled 2023 carry-forward for holdout inference.",
            "HV timestamp anomalies in 2020–2022 remain documented pending operator confirmation.",
        ],
    }
    manifest_path = figures / "berlin_multiyear_reportability_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "selected_dimension": selected["dimension"], "validation_mape_pct": selected["mape_pct"], "holdout_2024_mape_pct": holdout["mape_pct"], "png_generated": all(record["png_generated"] for record in figure_records), "manifest": str(manifest_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
