#!/usr/bin/env python3
"""Generate a reportable annual demand map for Berlin districts.

The map joins the d=3 annual district allocation to the audited Umweltatlas
district geometries.  The spatial result is intentionally labelled as a
conditional allocation: the same ``j2023g`` shares are used as allocation
weights and as the annual spatial reference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "merlin-edm-berlin-district-map"
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import pandas as pd


REPO = Path(__file__).resolve().parents[1]
DEFAULT_GEOMETRY = (
    REPO
    / "prototipo_3/data/de_alemania/external_validation/berlin_2023/"
    / "berlin_strom_districts.geojson"
)
DEFAULT_ANNUAL = (
    REPO
    / "corfo-report/validation/berlin/inference_2023/"
    / "berlin_district_allocation_2023.csv"
)
DEFAULT_HOURLY = (
    REPO
    / "prototipo_3/data/de_alemania/berlin_district_inference_2023/"
    / "berlin_district_d3_inference_2023.csv"
)
DEFAULT_OUTPUT = REPO / "corfo-report/results/figures"
EXPECTED_DISTRICTS = 12
EXPECTED_HOURS = 8_760


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", type=Path, default=DEFAULT_GEOMETRY)
    parser.add_argument("--annual", type=Path, default=DEFAULT_ANNUAL)
    parser.add_argument("--hourly", type=Path, default=DEFAULT_HOURLY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def validate_and_join(geometry_path: Path, annual_path: Path) -> gpd.GeoDataFrame:
    if not geometry_path.is_file():
        raise FileNotFoundError(f"Missing district geometry: {geometry_path}")
    if not annual_path.is_file():
        raise FileNotFoundError(f"Missing annual district table: {annual_path}")

    districts = gpd.read_file(geometry_path)
    annual = pd.read_csv(annual_path, dtype={"id_bezirk": str})
    for frame_name, frame in (("geometry", districts), ("annual", annual)):
        if "id_bezirk" not in frame.columns:
            raise ValueError(f"{frame_name} input lacks id_bezirk")
        frame["id_bezirk"] = frame["id_bezirk"].astype(str).str.zfill(2)

    if len(districts) != EXPECTED_DISTRICTS:
        raise ValueError(f"Expected {EXPECTED_DISTRICTS} district geometries, got {len(districts)}")
    if len(annual) != EXPECTED_DISTRICTS:
        raise ValueError(f"Expected {EXPECTED_DISTRICTS} annual rows, got {len(annual)}")
    if districts["id_bezirk"].duplicated().any() or annual["id_bezirk"].duplicated().any():
        raise ValueError("District identifiers must be unique in both inputs")
    if "bezirk" in districts.columns and "bezirk" in annual.columns:
        names = districts[["id_bezirk", "bezirk"]].merge(
            annual[["id_bezirk", "bezirk"]],
            on="id_bezirk",
            how="inner",
            suffixes=("_geometry", "_annual"),
            validate="one_to_one",
        )
        if (names["bezirk_geometry"] != names["bezirk_annual"]).any():
            raise ValueError("District names differ between geometry and annual table")
        annual = annual.drop(columns=["bezirk"])
    if districts.crs is None:
        raise ValueError("District geometry has no CRS")
    if districts.geometry.isna().any() or districts.geometry.is_empty.any():
        raise ValueError("District geometry contains null or empty geometries")

    value_column = "predicted_district_GWh_complete_rows"
    if value_column not in annual.columns:
        raise ValueError(f"Annual table lacks {value_column}")
    annual[value_column] = pd.to_numeric(annual[value_column], errors="raise")
    if not annual[value_column].map(pd.notna).all() or (annual[value_column] < 0).any():
        raise ValueError("Annual district demand must be finite and non-negative")

    joined = districts.merge(annual, on="id_bezirk", how="left", validate="one_to_one")
    if joined[value_column].isna().any():
        missing = joined.loc[joined[value_column].isna(), "id_bezirk"].tolist()
        raise ValueError(f"Annual table does not cover district IDs: {missing}")
    return joined


def relative_or_absolute(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def audit_hourly(hourly_path: Path) -> dict[str, object]:
    if not hourly_path.is_file():
        return {"available": False, "path": relative_or_absolute(hourly_path), "n_unique_hours": None, "coverage_pct": None}
    columns = ["timestamp_hour_end_utc", "id_bezirk", "district_predicted_MW"]
    hourly = pd.read_csv(hourly_path, usecols=columns, dtype={"id_bezirk": str})
    hourly["id_bezirk"] = hourly["id_bezirk"].astype(str).str.zfill(2)
    n_hours = int(hourly["timestamp_hour_end_utc"].nunique())
    n_districts = int(hourly["id_bezirk"].nunique())
    if n_districts != EXPECTED_DISTRICTS:
        raise ValueError(f"Hourly output covers {n_districts} districts, expected {EXPECTED_DISTRICTS}")
    if hourly["district_predicted_MW"].isna().any():
        raise ValueError("Hourly district output contains missing predictions")
    return {
        "available": True,
        "path": relative_or_absolute(hourly_path),
        "sha256": sha256(hourly_path),
        "n_unique_hours": n_hours,
        "expected_hours": EXPECTED_HOURS,
        "coverage_pct": n_hours / EXPECTED_HOURS * 100.0,
        "n_rows": int(len(hourly)),
        "n_districts": n_districts,
    }


def normalize_svg_whitespace(path: Path) -> None:
    """Remove generator-only trailing spaces so SVG checks remain clean."""
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")


def make_map(joined: gpd.GeoDataFrame, hourly_audit: dict[str, object], output_path: Path) -> None:
    value_column = "predicted_district_GWh_complete_rows"
    values = joined[value_column]
    vmin, vmax = float(values.min()), float(values.max())
    norm = Normalize(vmin=vmin, vmax=vmax)

    fig, ax = plt.subplots(figsize=(10, 10), constrained_layout=False)
    joined.plot(
        ax=ax,
        column=value_column,
        cmap="YlOrRd",
        norm=norm,
        edgecolor="#404040",
        linewidth=0.8,
    )
    joined.boundary.plot(ax=ax, color="#333333", linewidth=0.35)

    for _, row in joined.iterrows():
        point = row.geometry.representative_point()
        ax.annotate(
            f"{row['id_bezirk']}\n{row['bezirk']}",
            xy=(point.x, point.y),
            ha="center",
            va="center",
            fontsize=7.2,
            color="#171717",
            bbox={"boxstyle": "round,pad=0.18", "facecolor": "white", "alpha": 0.72, "edgecolor": "none"},
        )

    sm = ScalarMappable(norm=norm, cmap="YlOrRd")
    sm.set_array([])
    colorbar = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.045, pad=0.055)
    colorbar.set_label("Demanda anual reconstruida por distrito (GWh)")
    ax.set_axis_off()

    title = "Berlín: demanda eléctrica anual reconstruida por distrito (2023, d=3)"
    subtitle = "Asignación fija mediante shares anuales Umweltatlas j2023g"
    if hourly_audit.get("available"):
        subtitle += (
            f" · cobertura: {hourly_audit['n_unique_hours']:,}/{EXPECTED_HOURS:,} horas"
            .replace(",", ".")
        )
    fig.suptitle(title, fontsize=15, fontweight="bold", y=0.965)
    fig.text(0.5, 0.932, subtitle, ha="center", va="center", fontsize=10, color="#444444")
    fig.text(
        0.5,
        0.015,
        "Resultado espacial condicionado: los shares distritales se usan como pesos de desagregación; "
        "no constituye validación horaria distrital independiente.",
        ha="center",
        va="bottom",
        fontsize=8.2,
        color="#555555",
    )
    fig.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        metadata={"Date": None},
    )
    plt.close(fig)


def main() -> None:
    args = parse_args()
    geometry_path = args.geometry.resolve()
    annual_path = args.annual.resolve()
    hourly_path = args.hourly.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    joined = validate_and_join(geometry_path, annual_path)
    hourly = audit_hourly(hourly_path)
    stem = "berlin_demanda_distrital_d3_2023"
    png_path = output_dir / f"{stem}.png"
    svg_path = output_dir / f"{stem}.svg"
    make_map(joined, hourly, png_path)
    # SVG is produced separately so it remains useful in presentations and reports.
    make_map(joined, hourly, svg_path)
    normalize_svg_whitespace(svg_path)

    manifest = {
        "dataset": stem,
        "status": "generated",
        "territory": "Berlin, 12 Bezirke",
        "year": 2023,
        "model": "d=3",
        "value_column": "predicted_district_GWh_complete_rows",
        "units": "GWh",
        "allocation_rule": "annual_umweltatlas_share_2023",
        "spatial_interpretation": "conditional_allocation_not_independent_spatial_kpi",
        "geometry": {
            "path": str(geometry_path.relative_to(REPO)),
            "sha256": sha256(geometry_path),
            "crs": str(joined.crs),
            "features": int(len(joined)),
        },
        "annual_input": {
            "path": str(annual_path.relative_to(REPO)),
            "sha256": sha256(annual_path),
            "rows": int(len(joined)),
            "predicted_total_GWh": float(joined["predicted_district_GWh_complete_rows"].sum()),
        },
        "hourly_audit": hourly,
        "software": {
            "geopandas": gpd.__version__,
            "pandas": pd.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "outputs": {
            "png": {"path": str(png_path.relative_to(REPO)), "sha256": sha256(png_path)},
            "svg": {"path": str(svg_path.relative_to(REPO)), "sha256": sha256(svg_path)},
        },
    }
    manifest_path = output_dir / f"{stem}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
