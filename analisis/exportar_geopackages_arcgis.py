#!/usr/bin/env python3
"""Create ArcGIS-ready GeoPackages without modifying source artifacts.

The export keeps the original Parquet, CSV and GeoJSON files untouched.  It
creates spatial annual layers where a verified territorial geometry exists and
stores the complete hourly predictions as non-spatial GeoPackage tables.  The
latter avoids duplicating the same polygon millions of times while retaining
the hourly data for ArcGIS joins and time-enabled views.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import shutil
import sqlite3
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

import pandas as pd
import pyarrow.parquet as parquet


REPO = Path(__file__).resolve().parents[1]
CHILE_REPO = Path("/srv/compartido/inbox/MERLIN_EDM")
CHILE_EXTERNAL = Path("/srv/compartido/inbox/MERLIN_EDM_GIS_exports/chile")
GERMANY_OUTPUT = REPO / "corfo-report/results/geopackages/berlin_demanda_arcgis.gpkg"
GERMANY_MANIFEST = REPO / "corfo-report/results/geopackages/berlin_demanda_arcgis_manifest.json"
CHILE_OUTPUT = CHILE_EXTERNAL / "chile_demanda_arcgis.gpkg"
CHILE_MANIFEST = CHILE_EXTERNAL / "chile_demanda_arcgis_manifest.json"


def run_ogr(args: list[str]) -> None:
    command = ["ogr2ogr", *args]
    completed = subprocess.run(command, check=False, text=True, capture_output=True)
    if completed.returncode:
        raise RuntimeError(f"{command!r}\nstdout={completed.stdout}\nstderr={completed.stderr}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def normalize_value(value):
    if value is None:
        return None
    if hasattr(value, "isoformat") and not isinstance(value, (str, bytes)):
        return value.isoformat()
    if isinstance(value, float) and pd.isna(value):
        return None
    return value


def normalized_field(name: str) -> str:
    replacements = {"año": "year", "demanda_MWh": "demand_MWh", "demanda_": "demand_"}
    for source, target in replacements.items():
        name = name.replace(source, target)
    return name


def infer_sql_type(values: list[object]) -> str:
    non_null = [value for value in values if value not in (None, "")]
    if not non_null:
        return "TEXT"
    if all(isinstance(value, bool) or isinstance(value, int) for value in non_null):
        return "INTEGER"
    if all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in non_null):
        return "REAL"
    integer = re.compile(r"^[+-]?\d+$")
    decimal = re.compile(r"^[+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][+-]?\d+)?$")
    if all(integer.match(str(value)) for value in non_null):
        return "INTEGER"
    if all(decimal.match(str(value)) for value in non_null):
        return "REAL"
    return "TEXT"


def cast_for_sql(value, sql_type: str):
    value = normalize_value(value)
    if value in (None, ""):
        return None
    if sql_type == "INTEGER":
        return int(value)
    if sql_type == "REAL":
        return float(value)
    return str(value)


def parse_csv_value(value: str | None):
    if value is None or value == "":
        return None
    if re.fullmatch(r"[+-]?\d+", value):
        return int(value)
    if re.fullmatch(r"[+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][+-]?\d+)?", value):
        return float(value)
    return value


def register_attribute_table(conn: sqlite3.Connection, table: str, description: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    conn.execute(
        "INSERT INTO gpkg_contents "
        "(table_name,data_type,identifier,description,last_change,min_x,min_y,max_x,max_y,srs_id) "
        "VALUES (?,?,?,?,?,?,?,?,?,NULL)",
        (table, "attributes", table, description, now, None, None, None, None),
    )


def create_attribute_table(
    gpkg: Path,
    table: str,
    columns: list[str],
    rows: Iterable[dict[str, object]],
    description: str,
    indexes: Iterable[str] = (),
) -> int:
    """Write a non-spatial GeoPackage table from a streaming row iterator."""
    iterator = iter(rows)
    first_batch = []
    for _ in range(500):
        try:
            first_batch.append(next(iterator))
        except StopIteration:
            break
    if not first_batch:
        raise ValueError(f"No rows for table {table}")
    sample = {column: [row.get(column) for row in first_batch] for column in columns}
    sql_types = {column: infer_sql_type(values) for column, values in sample.items()}
    conn = sqlite3.connect(gpkg)
    try:
        conn.execute(f"DROP TABLE IF EXISTS {quote_identifier(table)}")
        definition = ", ".join(f"{quote_identifier(column)} {sql_types[column]}" for column in columns)
        conn.execute(f"CREATE TABLE {quote_identifier(table)} ({definition})")
        placeholders = ",".join("?" for _ in columns)
        insert = f"INSERT INTO {quote_identifier(table)} VALUES ({placeholders})"

        def insert_rows(batch: list[dict[str, object]]) -> None:
            conn.executemany(
                insert,
                [tuple(cast_for_sql(row.get(column), sql_types[column]) for column in columns) for row in batch],
            )

        insert_rows(first_batch)
        count = len(first_batch)
        batch = []
        for row in iterator:
            batch.append(row)
            if len(batch) >= 5000:
                insert_rows(batch)
                count += len(batch)
                batch.clear()
        if batch:
            insert_rows(batch)
            count += len(batch)
        register_attribute_table(conn, table, description)
        for column in indexes:
            if column in columns:
                index_name = f"idx_{table}_{column}"[:60]
                conn.execute(
                    f"CREATE INDEX {quote_identifier(index_name)} ON {quote_identifier(table)} ({quote_identifier(column)})"
                )
        conn.commit()
        return count
    finally:
        conn.close()


def parquet_rows(path: Path, rename: dict[str, str] | None = None) -> tuple[list[str], Iterator[dict[str, object]]]:
    parquet_file = parquet.ParquetFile(path)
    source_columns = list(parquet_file.schema.names)
    rename = rename or {}
    columns = [rename.get(column, normalized_field(column)) for column in source_columns]

    def iterator() -> Iterator[dict[str, object]]:
        for batch in parquet_file.iter_batches(batch_size=100_000):
            for row in batch.to_pylist():
                yield {rename.get(column, normalized_field(column)): normalize_value(row.get(column)) for column in source_columns}

    return columns, iterator()


def csv_rows(path: Path) -> tuple[list[str], Iterator[dict[str, object]]]:
    opener = gzip.open if path.suffix == ".gz" else open

    def iterator() -> Iterator[dict[str, object]]:
        with opener(path, "rt", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                yield {key: value for key, value in row.items()}

    with opener(path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        columns = next(reader)
    return columns, iterator()


def convert_gpkg_layer(source: Path, output: Path, source_layer: str | None, target_layer: str, first: bool) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    args = ["-f", "GPKG", str(output), str(source)]
    if source_layer:
        args.extend(["-sql", f"SELECT * FROM {quote_identifier(source_layer)}"])
    args.extend(["-nln", target_layer, "-lco", "GEOMETRY_NAME=geom"])
    if first:
        args.append("-overwrite")
    else:
        args.append("-update")
    run_ogr(args)


def convert_geojson_layer(source: Path, output: Path, target_layer: str, first: bool) -> None:
    args = ["-f", "GPKG", str(output), str(source), "-nln", target_layer, "-nlt", "MULTIPOLYGON", "-lco", "GEOMETRY_NAME=geom"]
    args.append("-overwrite" if first else "-update")
    run_ogr(args)


def load_geojson(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_geojson(path: Path, template: dict, features: list[dict]) -> None:
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features, "crs": template.get("crs")}, ensure_ascii=False), encoding="utf-8")


def geometry_feature_collection(template_path: Path, rows: list[dict[str, object]], key: str, properties: list[str]) -> Path:
    template = load_geojson(template_path)
    by_key: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        by_key.setdefault(str(row[key]).zfill(2), []).append(row)
    features = []
    for feature in template["features"]:
        source_props = feature.get("properties", {})
        feature_key = str(source_props.get("id_bezirk", source_props.get("id", ""))).zfill(2)
        if feature_key not in by_key:
            raise ValueError(f"No result row for geometry key {feature_key}")
        for row in by_key[feature_key]:
            properties_out = {property_name: row.get(property_name) for property_name in properties}
            features.append({"type": "Feature", "geometry": feature["geometry"], "properties": properties_out})
    return {"type": "FeatureCollection", "features": features, "crs": template.get("crs")}


def write_temp_geojson(payload: dict, directory: Path, name: str) -> Path:
    path = directory / name
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def germany_export() -> dict[str, object]:
    output = GERMANY_OUTPUT
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing export: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    base_geometry = REPO / "prototipo_3/data/de_alemania/external_validation/berlin_2023/berlin_strom_districts.geojson"
    district_csv = REPO / "corfo-report/results/tables/berlin_multiyear_d8_district_annual.csv"
    sector_csv = REPO / "corfo-report/results/tables/berlin_multiyear_d8_district_sector_annual.csv"
    annual_csv = REPO / "corfo-report/results/tables/berlin_multiyear_d8_annual_summary.csv"
    hourly_d8 = REPO / "prototipo_3/data/de_alemania/berlin_multiyear_inference_d8/berlin_multiyear_d8_inference.csv.gz"
    hourly_d3 = REPO / "prototipo_3/data/de_alemania/berlin_inference_2023/berlin_d3_inference_2023.csv"
    for path in (base_geometry, district_csv, sector_csv, annual_csv, hourly_d8, hourly_d3):
        if not path.is_file():
            raise FileNotFoundError(path)
    with tempfile.TemporaryDirectory(prefix="merlin_berlin_gpkg_") as temp_dir:
        temp = Path(temp_dir)
        district_rows = [
            {key: parse_csv_value(value) for key, value in row.items()}
            for row in csv.DictReader(district_csv.open(encoding="utf-8", newline=""))
        ]
        sector_rows = [
            {key: parse_csv_value(value) for key, value in row.items()}
            for row in csv.DictReader(sector_csv.open(encoding="utf-8", newline=""))
        ]
        district_props = list(district_rows[0])
        sector_props = list(sector_rows[0])
        district_geojson = write_temp_geojson(
            geometry_feature_collection(base_geometry, district_rows, "id_bezirk", district_props), temp, "district_annual.geojson"
        )
        sector_geojson = write_temp_geojson(
            geometry_feature_collection(base_geometry, sector_rows, "id_bezirk", sector_props), temp, "district_sector_annual.geojson"
        )
        convert_geojson_layer(district_geojson, output, "berlin_d8_district_annual", first=True)
        convert_geojson_layer(sector_geojson, output, "berlin_d8_district_sector_annual", first=False)
    table_specs = [
        ("berlin_d8_annual_summary", annual_csv, "csv", ["year"]),
        ("berlin_d8_hourly", hourly_d8, "csv", ["source_year", "timestamp_hour_end_utc", "split"]),
        ("berlin_d3_hourly_historical", hourly_d3, "csv", ["split", "timestamp_hour_end_utc"]),
    ]
    table_counts = {}
    for table, path, kind, indexes in table_specs:
        columns, rows = csv_rows(path)
        table_counts[table] = create_attribute_table(output, table, columns, rows, f"MERLIN EDM Germany result table: {table}", indexes)
    return {
        "path": str(output),
        "sha256": sha256(output),
        "layers": ["berlin_d8_district_annual", "berlin_d8_district_sector_annual"],
        "tables": table_counts,
        "crs": "EPSG:25833",
        "sources": [{"path": str(path), "sha256": sha256(path)} for path in (base_geometry, district_csv, sector_csv, annual_csv, hourly_d8, hourly_d3)],
        "spatial_interpretation": "Annual district and district-sector layers are conditional allocations, not independent spatial observations.",
    }


def chile_export() -> dict[str, object]:
    output = CHILE_OUTPUT
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing export: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    regional_annual = Path("/srv/compartido/inbox/datos_modelos_MERLIN_EDM_prot_3/data/rec_2024_2025/results/capas_regionales/wp2_output_demanda_electrica_regional.gpkg")
    communal_annual = Path("/srv/compartido/inbox/datos_modelos_MERLIN_EDM_prot_3/data/rec_2024_2025/results/capas_comunales/wp2_output_demanda_electrica_comunal.gpkg")
    regional_2023 = CHILE_REPO / "prototipo_3/data/rec_historica/2023/demanda_regional_2023_horaria.parquet"
    regional_2024_25 = Path("/srv/compartido/inbox/datos_modelos_MERLIN_EDM_prot_3/data/rec_2024_2025/results/capas_regionales/wp2_output_demanda_electrica_regional_ts.parquet")
    communal_2024_25 = Path("/srv/compartido/inbox/datos_modelos_MERLIN_EDM_prot_3/data/rec_2024_2025/results/capas_comunales/wp2_output_demanda_electrica_comunal_ts.parquet")
    raw_regional = Path("/srv/compartido/inbox/datos_modelos_MERLIN_EDM_prot_3/data/raw/capa_regional.gpkg")
    for path in (regional_annual, communal_annual, regional_2023, regional_2024_25, communal_2024_25, raw_regional):
        if not path.is_file():
            raise FileNotFoundError(path)
    regional_layer = "wp2_output_demanda_electrica_regional"
    communal_layer = "wp2_output_demanda_electrica_comunal"
    convert_gpkg_layer(regional_annual, output, regional_layer, regional_layer, first=True)
    convert_gpkg_layer(communal_annual, output, communal_layer, communal_layer, first=False)
    table_specs = [
        ("chile_regional_hourly_2023", regional_2023),
        ("chile_regional_hourly_2024_2025", regional_2024_25),
        ("chile_comunal_hourly_2024_2025", communal_2024_25),
    ]
    table_counts = {}
    for table, path in table_specs:
        columns, rows = parquet_rows(path)
        indexes = [column for column in ("timestamp", "year", "region", "comuna") if column in columns]
        table_counts[table] = create_attribute_table(output, table, columns, rows, f"MERLIN EDM Chile result table: {table}", indexes)
    return {
        "path": str(output),
        "sha256": sha256(output),
        "layers": [regional_layer, communal_layer],
        "tables": table_counts,
        "crs": "EPSG:4326 (result layers)",
        "sources": [{"path": str(path), "sha256": sha256(path)} for path in (regional_annual, communal_annual, regional_2023, regional_2024_25, communal_2024_25, raw_regional)],
        "note": "The original Chile repository and source files were not modified; this export is outside that repository.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-chile", action="store_true")
    parser.add_argument("--skip-germany", action="store_true")
    args = parser.parse_args()
    previous_manifest = {}
    if GERMANY_MANIFEST.is_file():
        previous_manifest = json.loads(GERMANY_MANIFEST.read_text(encoding="utf-8"))
    results = {}
    if not args.skip_germany:
        results["germany"] = germany_export()
    else:
        results["germany"] = previous_manifest.get("germany")
    if not args.skip_chile:
        results["chile"] = chile_export()
    else:
        results["chile"] = previous_manifest.get("chile")
    manifest = {
        "export": "MERLIN_EDM ArcGIS GeoPackage copies",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "originals_preserved": True,
        "germany": results.get("germany"),
        "chile": results.get("chile"),
        "limitations": [
            "Hourly records are stored as non-spatial GeoPackage attribute tables; geometry is not duplicated per hour.",
            "A GIS user can join the hourly tables to the territorial layers using the documented keys.",
            "Berlin district and district-sector values remain conditional proxy allocations.",
        ],
    }
    GERMANY_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    GERMANY_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CHILE_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    CHILE_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
