#!/usr/bin/env python3
"""Infer d=8 for 2020-2024 and generate Berlin district/sector annual maps.

The selected multiyear model produces one Berlin aggregate hourly prediction.
This script preserves that prediction and applies the documented spatial
post-processing rule:

    district_energy[y,d] = Berlin_energy[y] * district_weight_2023[d]
    sector_energy[y,d,s] = district_energy[y,d] * sector_share[y,s]

District weights are fixed at the audited 2023 Umweltatlas proxy because no
annual district series is available. Sector shares are annual Strombilanz
shares; 2024 is the labelled 2023 carry-forward used by the frozen holdout.
The resulting maps are therefore conditional allocation scenarios, not
independent spatial or district-sector observations.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import io
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import pandas as pd

from desagregacion_distrito_sector_berlin_2023 import (
    SECTOR_FIGURE_NAMES,
    SECTOR_ORDER,
    centroid,
    color_for,
    load_geometry,
    outer_path,
    transform_factory,
)


REPO = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = REPO / "prototipo_3/data/de_alemania"
DEFAULT_MODEL_ROOT = DEFAULT_DATA_ROOT / "berlin_training_multiyear"
DEFAULT_FEATURES = DEFAULT_DATA_ROOT / "berlin_multiyear/berlin_hv_temperature_features_2020_2024.csv"
DEFAULT_PROXY = REPO / "corfo-report/validation/berlin/berlin_district_sector_proxy_2023.csv"
DEFAULT_SHARES = REPO / "corfo-report/validation/berlin/berlin_sector_shares_multiyear_2020_2024.csv"
DEFAULT_GEOMETRY = DEFAULT_DATA_ROOT / "external_validation/berlin_2023/berlin_strom_districts.geojson"
DEFAULT_OUTPUT_DATA = DEFAULT_DATA_ROOT / "berlin_multiyear_inference_d8"
DEFAULT_TABLES = REPO / "corfo-report/results/tables"
DEFAULT_FIGURES = REPO / "corfo-report/results/figures"
DEFAULT_REPORT = REPO / "corfo-report/validation/berlin/multiyear_2020_2024"
SPLIT_YEARS = {"train": (2020, 2021, 2022), "validation": (2023,), "test": (2024,)}
YEARS = (2020, 2021, 2022, 2023, 2024)
PALETTE_ANCHORS = ((255, 255, 204), (255, 237, 160), (254, 217, 118), (254, 178, 76), (253, 141, 60), (252, 78, 42), (227, 26, 28), (189, 0, 38), (128, 0, 38))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".gz":
        raw = gzip.GzipFile(filename=str(path), mode="wb", mtime=0)
        handle = io.TextIOWrapper(raw, encoding="utf-8", newline="")
    else:
        handle = path.open("w", encoding="utf-8", newline="")
    with handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: object) -> object:
    return f"{value:.9f}" if isinstance(value, float) else value


def load_model_predictions(model_root: Path, features_path: Path) -> tuple[pd.DataFrame, dict[str, object], Path]:
    import numpy as np
    import tensorflow as tf

    manifest_path = model_root / "berlin_training_contract_multiyear_d8_manifest.json"
    model_path = model_root / "model_multiyear_d8/best_merlin_mlp_berlin_multiyear_d8.keras"
    if not manifest_path.is_file() or not model_path.is_file():
        raise FileNotFoundError(f"Missing d=8 manifest or weights: {manifest_path}, {model_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    features = manifest["features"]
    mu = float(manifest["scaling"]["mu_train_MW"])
    sigma = float(manifest["scaling"]["sigma_train_MW"])
    source = pd.read_csv(features_path)
    source["source_year"] = pd.to_numeric(source["source_year"], errors="raise").astype(int)
    source["temperature_complete_8lags"] = pd.to_numeric(source["temperature_complete_8lags"], errors="raise").astype(int)
    source_complete = source[source["temperature_complete_8lags"] == 1].reset_index(drop=True)
    model = tf.keras.models.load_model(model_path, compile=False)
    output_frames: list[pd.DataFrame] = []
    for split, years in SPLIT_YEARS.items():
        contract_path = model_root / f"berlin_multiyear_d8_{split}.parquet"
        contract = pd.read_parquet(contract_path, engine="pyarrow")
        metadata = source_complete[source_complete["source_year"].isin(years)].reset_index(drop=True)
        if len(contract) != len(metadata):
            raise ValueError(f"Contract/source row mismatch for {split}: {len(contract)} != {len(metadata)}")
        actual = contract["target_scaled"].to_numpy(dtype=float) * sigma + mu
        source_actual = metadata["load_mean_MW"].to_numpy(dtype=float)
        if not np.allclose(actual, source_actual, rtol=0.0, atol=1e-8):
            raise ValueError(f"Target alignment failed for {split}")
        prediction_scaled = model.predict(contract[features].to_numpy(dtype=np.float32), batch_size=2048, verbose=0).ravel()
        frame = metadata[["source_year", "timestamp_hour_end_utc", "timestamp_hour_end_local", "load_mean_MW", "energy_MWh"]].copy()
        frame["split"] = split
        frame["load_predicted_MW"] = prediction_scaled.astype(float) * sigma + mu
        frame["prediction_error_MW"] = frame["load_predicted_MW"] - frame["load_mean_MW"]
        frame["coverage_flag"] = "complete_d8_features"
        output_frames.append(frame)
    result = pd.concat(output_frames, ignore_index=True).sort_values("timestamp_hour_end_utc").reset_index(drop=True)
    return result, manifest, model_path


def font(size: int):
    from PIL import ImageFont
    candidates = ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans.ttf")
    selected = next((path for path in candidates if Path(path).is_file()), None)
    return ImageFont.truetype(selected, size) if selected else ImageFont.load_default()


def draw_map_png(draw, districts, values: dict[str, float], x0: float, y0: float, width: float, height: float, minimum: float, maximum: float, labels: bool = True) -> None:
    transform = transform_factory(districts, x0, y0, width, height)
    for district in districts:
        color = color_for(values[district["id_bezirk"]], minimum, maximum)
        for polygon in district["polygons"]:
            ring = polygon[0]
            draw.polygon([transform(point) for point in ring], fill=color, outline="#3d3d3d")
        if labels:
            px, py = centroid(district, transform)
            draw.text((px, py), district["id_bezirk"], fill="#171717", anchor="mm", font=font(12))


def draw_colorbar_png(draw, x: float, y: float, width: float, height: float, minimum: float, maximum: float, label: str) -> None:
    draw.text((x + width / 2, y - 10), label, fill="#555555", anchor="ms", font=font(13))
    for offset in range(int(width)):
        ratio = offset / max(width - 1, 1)
        value = minimum + ratio * (maximum - minimum)
        draw.line((x + offset, y, x + offset, y + height), fill=color_for(value, minimum, maximum))
    draw.rectangle((x, y, x + width, y + height), outline="#555555", width=1)
    for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
        tick_x = x + fraction * width
        value = minimum + fraction * (maximum - minimum)
        draw.line((tick_x, y + height, tick_x, y + height + 6), fill="#555555", width=1)
        draw.text((tick_x, y + height + 9), f"{value:.1f}", fill="#555555", anchor="ma", font=font(12))


def render_district_png(path: Path, districts, values: dict[tuple[int, str], float], minimum: float, maximum: float) -> None:
    from PIL import Image, ImageDraw
    width, height = 2350, 720
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((width / 2, 26), "Berlín: demanda anual reconstruida por distrito — expansión multianual d=8", fill="#171717", anchor="ma", font=font(26))
    draw.text((width / 2, 65), "2020–2024 · GWh · pesos distritales fijos del proxy Umweltatlas 2023", fill="#4b4b4b", anchor="ma", font=font(17))
    for index, year in enumerate(YEARS):
        x = 30 + index * 465
        draw.text((x + 205, 105), str(year), fill="#202020", anchor="ma", font=font(20))
        draw_map_png(draw, districts, {district["id_bezirk"]: values[(year, district["id_bezirk"])] for district in districts}, x, 135, 410, 430, minimum, maximum)
    draw_colorbar_png(draw, 875, 595, 600, 18, minimum, maximum, "Demanda anual reconstruida (GWh)")
    draw.text((width / 2, 675), "Asignación condicional: predicción agregada d=8 × district_weight 2023; no constituye un KPI espacial independiente.", fill="#555555", anchor="ma", font=font(13))
    image.save(path, format="PNG", optimize=True)


def render_sector_png(path: Path, districts, values: dict[tuple[int, str, str], float], minimum: float, maximum: float) -> None:
    from PIL import Image, ImageDraw
    width, height = 2350, 1860
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((width / 2, 24), "Berlín: demanda anual reconstruida por distrito y sector — expansión multianual d=8", fill="#171717", anchor="ma", font=font(25))
    draw.text((width / 2, 61), "Shares sectoriales Strombilanz por año · distribución distrital fija 2023 · GWh", fill="#4b4b4b", anchor="ma", font=font(16))
    for row, sector in enumerate(SECTOR_ORDER):
        for column, year in enumerate(YEARS):
            x, y = 25 + column * 465, 95 + row * 335
            draw.text((x + 205, y), f"{year} · {sector} - {SECTOR_FIGURE_NAMES[sector]}", fill="#202020", anchor="ma", font=font(14))
            draw_map_png(draw, districts, {district["id_bezirk"]: values[(year, district["id_bezirk"], sector)] for district in districts}, x, y + 26, 410, 265, minimum, maximum)
    draw_colorbar_png(draw, 875, 1740, 600, 18, minimum, maximum, "Demanda anual reconstruida por distrito-sector (GWh)")
    draw.text((width / 2, 1830), "Público = 0 porque Strombilanz no permite separarlo; la asignación es un escenario condicionado, no una medición distrito-sector.", fill="#555555", anchor="ma", font=font(13))
    image.save(path, format="PNG", optimize=True)


def svg_text(x: float, y: float, value: object, size: int, anchor: str = "middle", weight: str = "normal", fill: str = "#202020") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-family="DejaVu Sans,Arial,sans-serif" font-size="{size}px" font-weight="{weight}" fill="{fill}">{html.escape(str(value))}</text>'


def colorbar_svg(x: float, y: float, width: float, height: float, minimum: float, maximum: float, label: str) -> list[str]:
    chunks = [svg_text(x + width / 2, y - 10, label, 13, fill="#555555")]
    for step in range(100):
        fraction = step / 99
        value = minimum + fraction * (maximum - minimum)
        chunks.append(f'<rect x="{x + step * width / 100:.2f}" y="{y:.1f}" width="{width / 100 + 0.1:.2f}" height="{height:.1f}" fill="{color_for(value, minimum, maximum)}"/>')
    chunks.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" fill="none" stroke="#555555" stroke-width="1"/>')
    for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
        tick_x = x + fraction * width
        value = minimum + fraction * (maximum - minimum)
        chunks.append(f'<line x1="{tick_x:.1f}" y1="{y + height:.1f}" x2="{tick_x:.1f}" y2="{y + height + 6:.1f}" stroke="#555555" stroke-width="1"/>')
        chunks.append(svg_text(tick_x, y + height + 22, f"{value:.1f}", 12, fill="#555555"))
    return chunks


def render_district_svg(path: Path, districts, values: dict[tuple[int, str], float], minimum: float, maximum: float) -> None:
    width, height = 2350, 720
    chunks = ['<?xml version="1.0" encoding="UTF-8"?>', f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="white"/>', svg_text(width / 2, 40, "Berlín: demanda anual reconstruida por distrito — expansión multianual d=8", 25, weight="bold"), svg_text(width / 2, 72, "2020–2024 · GWh · pesos distritales fijos del proxy Umweltatlas 2023", 17, fill="#4b4b4b")]
    for index, year in enumerate(YEARS):
        x = 30 + index * 465
        chunks.append(svg_text(x + 205, 112, year, 20, weight="bold"))
        transform = transform_factory(districts, x, 140, 410, 430)
        for district in districts:
            color = color_for(values[(year, district["id_bezirk"])], minimum, maximum)
            chunks.append(f'<path d="{outer_path(district, transform)}" fill="{color}" fill-rule="evenodd" stroke="#3d3d3d" stroke-width="1.1"/>')
            px, py = centroid(district, transform)
            chunks.append(svg_text(px, py, district["id_bezirk"], 12))
    chunks.extend(colorbar_svg(875, 595, 600, 18, minimum, maximum, "Demanda anual reconstruida (GWh)"))
    chunks.extend([svg_text(width / 2, 675, "Asignación condicional: predicción agregada d=8 × district_weight 2023; no constituye un KPI espacial independiente.", 13, fill="#555555"), "</svg>"])
    path.write_text("\n".join(chunks) + "\n", encoding="utf-8")


def render_sector_svg(path: Path, districts, values: dict[tuple[int, str, str], float], minimum: float, maximum: float) -> None:
    width, height = 2350, 1860
    chunks = ['<?xml version="1.0" encoding="UTF-8"?>', f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="white"/>', svg_text(width / 2, 38, "Berlín: demanda anual reconstruida por distrito y sector — expansión multianual d=8", 24, weight="bold"), svg_text(width / 2, 69, "Shares sectoriales Strombilanz por año · distribución distrital fija 2023 · GWh", 16, fill="#4b4b4b")]
    for row, sector in enumerate(SECTOR_ORDER):
        for column, year in enumerate(YEARS):
            x, y = 25 + column * 465, 95 + row * 335
            chunks.append(svg_text(x + 205, y, f"{year} · {sector} - {SECTOR_FIGURE_NAMES[sector]}", 14, weight="bold"))
            transform = transform_factory(districts, x, y + 28, 410, 265)
            for district in districts:
                color = color_for(values[(year, district["id_bezirk"], sector)], minimum, maximum)
                chunks.append(f'<path d="{outer_path(district, transform)}" fill="{color}" fill-rule="evenodd" stroke="#3d3d3d" stroke-width="1.0"/>')
                px, py = centroid(district, transform)
                chunks.append(svg_text(px, py, district["id_bezirk"], 10))
    chunks.extend(colorbar_svg(875, 1740, 600, 18, minimum, maximum, "Demanda anual reconstruida por distrito-sector (GWh)"))
    chunks.extend([svg_text(width / 2, 1830, "Público = 0 porque Strombilanz no permite separarlo; la asignación es un escenario condicionado, no una medición distrito-sector.", 13, fill="#555555"), "</svg>"])
    path.write_text("\n".join(chunks) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--model-root", type=Path, default=DEFAULT_MODEL_ROOT)
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--proxy", type=Path, default=DEFAULT_PROXY)
    parser.add_argument("--shares", type=Path, default=DEFAULT_SHARES)
    parser.add_argument("--geometry", type=Path, default=DEFAULT_GEOMETRY)
    parser.add_argument("--output-data", type=Path, default=DEFAULT_OUTPUT_DATA)
    parser.add_argument("--tables", type=Path, default=DEFAULT_TABLES)
    parser.add_argument("--figures", type=Path, default=DEFAULT_FIGURES)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    for path in (args.features, args.proxy, args.shares, args.geometry):
        if not path.resolve().is_file():
            raise FileNotFoundError(path)
    args.output_data.resolve().mkdir(parents=True, exist_ok=True)
    args.tables.resolve().mkdir(parents=True, exist_ok=True)
    args.figures.resolve().mkdir(parents=True, exist_ok=True)
    args.report.resolve().mkdir(parents=True, exist_ok=True)

    inference, manifest, model_path = load_model_predictions(args.model_root.resolve(), args.features.resolve())
    inference_path = args.output_data.resolve() / "berlin_multiyear_d8_inference.csv.gz"
    write_csv(inference_path, list(inference.columns), ({column: fmt(row[column]) for column in inference.columns} for row in inference.to_dict("records")))

    proxy = read_csv(args.proxy.resolve())
    shares = read_csv(args.shares.resolve())
    districts = load_geometry(args.geometry.resolve())
    proxy_by_id = {str(row["id_bezirk"]).zfill(2): row for row in proxy}
    share_by_year = {int(row["year"]): row for row in shares}
    geometry_ids = {district["id_bezirk"] for district in districts}
    if set(proxy_by_id) != geometry_ids or set(share_by_year) != set(YEARS):
        raise ValueError("Proxy, geometry and annual shares do not cover the same expected scope")
    district_weights = {district_id: float(row["district_weight"]) for district_id, row in proxy_by_id.items()}
    if abs(sum(district_weights.values()) - 1.0) > 2e-9:
        raise ValueError("District weights do not sum to one")

    district_rows: list[dict[str, object]] = []
    sector_rows: list[dict[str, object]] = []
    year_summary: list[dict[str, object]] = []
    district_values: dict[tuple[int, str], float] = {}
    sector_values: dict[tuple[int, str, str], float] = {}
    for year in YEARS:
        year_frame = inference[inference["source_year"] == year]
        city_predicted = float(year_frame["load_predicted_MW"].sum() / 1000.0)
        city_observed = float(year_frame["load_mean_MW"].sum() / 1000.0)
        share_row = share_by_year[year]
        shares_by_sector = {sector: float(share_row[f"share_{sector}"]) for sector in SECTOR_ORDER}
        share_sum_error = sum(shares_by_sector.values()) - 1.0
        year_summary.append({"year": year, "split": str(year_frame["split"].iloc[0]), "n_complete_hours": len(year_frame), "observed_energy_GWh": city_observed, "predicted_energy_GWh": city_predicted, "predicted_minus_observed_pct": (city_predicted - city_observed) / city_observed * 100.0, "sector_share_sum_error": share_sum_error, "share_status": share_row["share_status"]})
        district_total = 0.0
        sector_total = 0.0
        for district in districts:
            district_id = district["id_bezirk"]
            district_energy = city_predicted * district_weights[district_id]
            district_total += district_energy
            district_values[(year, district_id)] = district_energy
            district_rows.append({"year": year, "id_bezirk": district_id, "bezirk": district["bezirk"], "city_predicted_GWh": city_predicted, "district_weight_2023": district_weights[district_id], "district_predicted_GWh": district_energy, "allocation_rule": "annual_umweltatlas_share_2023", "spatial_status": "conditional_allocation_not_independent_kpi"})
            for sector in SECTOR_ORDER:
                sector_energy = district_energy * shares_by_sector[sector]
                sector_total += sector_energy
                sector_values[(year, district_id, sector)] = sector_energy
                sector_rows.append({"year": year, "id_bezirk": district_id, "bezirk": district["bezirk"], "sector_code": sector, "sector_name": SECTOR_FIGURE_NAMES[sector], "city_predicted_GWh": city_predicted, "district_weight_2023": district_weights[district_id], "sector_share_annual": shares_by_sector[sector], "district_sector_predicted_GWh": sector_energy, "allocation_rule": "annual_umweltatlas_share_2023_times_annual_strombilanz_share", "spatial_sector_status": "conditional_allocation_not_independent_kpi"})
        year_summary[-1]["district_total_residual_GWh"] = district_total - city_predicted
        year_summary[-1]["district_sector_total_residual_GWh"] = sector_total - city_predicted

    district_path = args.tables.resolve() / "berlin_multiyear_d8_district_annual.csv"
    sector_path = args.tables.resolve() / "berlin_multiyear_d8_district_sector_annual.csv"
    summary_path = args.tables.resolve() / "berlin_multiyear_d8_annual_summary.csv"
    write_csv(district_path, list(district_rows[0]), ({key: fmt(row[key]) for key in district_rows[0]} for row in district_rows))
    write_csv(sector_path, list(sector_rows[0]), ({key: fmt(row[key]) for key in sector_rows[0]} for row in sector_rows))
    write_csv(summary_path, list(year_summary[0]), ({key: fmt(row[key]) for key in year_summary[0]} for row in year_summary))

    district_min, district_max = min(district_values.values()), max(district_values.values())
    sector_min, sector_max = min(sector_values.values()), max(sector_values.values())
    district_png = args.figures.resolve() / "berlin_demanda_distrital_multiyear_d8_2020_2024.png"
    district_svg = args.figures.resolve() / "berlin_demanda_distrital_multiyear_d8_2020_2024.svg"
    sector_png = args.figures.resolve() / "berlin_demanda_distrito_sector_anual_multiyear_d8_2020_2024.png"
    sector_svg = args.figures.resolve() / "berlin_demanda_distrito_sector_anual_multiyear_d8_2020_2024.svg"
    render_district_png(district_png, districts, district_values, district_min, district_max)
    render_district_svg(district_svg, districts, district_values, district_min, district_max)
    render_sector_png(sector_png, districts, sector_values, sector_min, sector_max)
    render_sector_svg(sector_svg, districts, sector_values, sector_min, sector_max)

    max_district_residual = max(abs(float(row["district_total_residual_GWh"])) for row in year_summary)
    max_sector_residual = max(abs(float(row["district_sector_total_residual_GWh"])) for row in year_summary)
    audit = {
        "dataset": "berlin_multiyear_d8_spatial_postprocess_2020_2024",
        "status": "pass" if max_district_residual <= 1e-6 and max_sector_residual <= 1e-6 else "review_required",
        "model_dimension": 8,
        "years": list(YEARS),
        "inference": {"path": relative(inference_path), "sha256": sha256(inference_path), "rows": len(inference), "hours_by_year": {str(row["year"]): row["n_complete_hours"] for row in year_summary}},
        "district_rule": "predicted_city_GWh * fixed_2023_Umweltatlas_district_weight",
        "sector_rule": "district_GWh * annual_Strombilanz_sector_share",
        "district_weights_source": {"path": relative(args.proxy.resolve()), "sha256": sha256(args.proxy.resolve()), "districts": len(districts)},
        "sector_shares_source": {"path": relative(args.shares.resolve()), "sha256": sha256(args.shares.resolve()), "temporal_resolution": "annual_broadcast", "share_status_2024": share_by_year[2024]["share_status"]},
        "controls": {"max_district_conservation_residual_GWh": max_district_residual, "max_district_sector_conservation_residual_GWh": max_sector_residual, "district_weight_sum_error": sum(district_weights.values()) - 1.0, "max_sector_share_sum_error": max(abs(float(row["sector_share_sum_error"])) for row in year_summary)},
        "outputs": {
            "district_table": {"path": relative(district_path), "sha256": sha256(district_path), "rows": len(district_rows)},
            "district_sector_table": {"path": relative(sector_path), "sha256": sha256(sector_path), "rows": len(sector_rows)},
            "annual_summary": {"path": relative(summary_path), "sha256": sha256(summary_path), "rows": len(year_summary)},
            "district_png": {"path": relative(district_png), "sha256": sha256(district_png)},
            "district_svg": {"path": relative(district_svg), "sha256": sha256(district_svg)},
            "sector_png": {"path": relative(sector_png), "sha256": sha256(sector_png)},
            "sector_svg": {"path": relative(sector_svg), "sha256": sha256(sector_svg)},
        },
        "limitations": [
            "No annual district measurement is available; 2023 Umweltatlas district weights are reused for all years.",
            "Sector shares are annual Strombilanz shares; 2024 is a labelled 2023 carry-forward for holdout only.",
            "Public share is zero because the available Strombilanz category does not separate public consumption.",
            "The maps are conditional allocation scenarios and do not establish independent district or district-sector KPIs.",
        ],
    }
    audit_json = args.report.resolve() / "berlin_multiyear_spatial_postprocess_audit.json"
    audit_json.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit_md = args.report.resolve() / "berlin_multiyear_spatial_postprocess_audit.md"
    lines = [
        "# Postproceso espacial y sectorial — expansión multianual Berlín d=8",
        "",
        "Se generaron mapas anuales por distrito y por distrito-sector para 2020–2024 a partir de la inferencia agregada seleccionada d=8.",
        "",
        "## Reglas",
        "",
        "- Distrito: `demanda_distrito_y = demanda_Berlín_y × district_weight_2023`.",
        "- Sector: `demanda_distrito_sector_y = demanda_distrito_y × share_sector_y`.",
        "- Los pesos distritales corresponden al proxy `j2023g` del Umweltatlas 2023 y se mantienen fijos por falta de una serie distrital anual compatible.",
        "- Los shares sectoriales provienen de Strombilanz y son anuales; 2024 usa carry-forward 2023 etiquetado.",
        "",
        "## Controles por año",
        "",
        "| Año | Horas completas | Energía observada (GWh) | Energía predicha (GWh) | Error predicho-observado (%) | Residuo distrito (GWh) | Residuo distrito-sector (GWh) | Share status |",
        "|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in year_summary:
        lines.append(f"| {row['year']} | {row['n_complete_hours']} | {row['observed_energy_GWh']:.6f} | {row['predicted_energy_GWh']:.6f} | {row['predicted_minus_observed_pct']:.6f} | {row['district_total_residual_GWh']:.3e} | {row['district_sector_total_residual_GWh']:.3e} | {row['share_status']} |")
    lines.extend([
        "",
        f"Residuos máximos de conservación: **{max_district_residual:.3e} GWh** a nivel distrito y **{max_sector_residual:.3e} GWh** a nivel distrito-sector.",
        "",
        "## Interpretación y limitaciones",
        "",
        "La conservación confirma que el postproceso reparte exactamente el agregado predicho. No demuestra que la red haya aprendido diferencias horarias entre distritos: el peso espacial es externo y fijo. La comparación espacial/sectorial debe presentarse como escenario condicionado hasta disponer de mediciones distritales independientes.",
        "",
        "Figuras: `corfo-report/results/figures/berlin_demanda_distrital_multiyear_d8_2020_2024.png` y `corfo-report/results/figures/berlin_demanda_distrito_sector_anual_multiyear_d8_2020_2024.png`.",
    ])
    audit_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": audit["status"], "rows_inference": len(inference), "district_rows": len(district_rows), "district_sector_rows": len(sector_rows), "max_district_residual_GWh": max_district_residual, "max_district_sector_residual_GWh": max_sector_residual, "district_figure": relative(district_png), "district_sector_figure": relative(sector_png), "audit": relative(audit_json)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
