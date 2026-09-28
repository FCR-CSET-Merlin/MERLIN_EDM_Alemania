"""Extract DWD hourly 2 m temperature for Berlin-Tempelhof, 2023.

DWD's station product is interpreted in UTC for this period according to its
metadata. The output keeps both UTC and Europe/Berlin representations and
records missing observations instead of silently imputing them.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[2]
UTC = timezone.utc
LOCAL_TZ = ZoneInfo("Europe/Berlin")
SOURCE_URL = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/"
    "climate/hourly/air_temperature/historical/"
    " "
)
# The file name is versioned by DWD; the URL is recorded in the manifest from
# the actual archive name passed to this script.
EXPECTED_ROWS = 365 * 24


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def product_member(names: list[str]) -> str:
    candidates = [name for name in names if re.match(r".*/?produkt_tu_stunde_.*\.txt$", name)]
    if len(candidates) != 1:
        raise ValueError(f"Expected one DWD product member, got {candidates}")
    return candidates[0]


def extract(zip_path: Path) -> tuple[list[dict[str, object]], dict[str, object], str]:
    with zipfile.ZipFile(zip_path) as archive:
        member = product_member(archive.namelist())
        rows: list[dict[str, object]] = []
        with archive.open(member) as binary:
            text = (line.decode("latin-1") for line in binary)
            reader = csv.DictReader(text, delimiter=";")
            for row in reader:
                stamp = row["MESS_DATUM"].strip()
                if not stamp.startswith("2023"):
                    continue
                timestamp_utc = datetime.strptime(stamp, "%Y%m%d%H").replace(tzinfo=UTC)
                raw_temp = row["TT_TU"].strip()
                value = None if raw_temp in {"-999", "-999.0", "-999.0"} else float(raw_temp)
                rows.append(
                    {
                        "station_id": row["STATIONS_ID"].strip(),
                        "timestamp_utc": timestamp_utc.isoformat(),
                        "timestamp_local": timestamp_utc.astimezone(LOCAL_TZ).isoformat(),
                        "temperature_C": "" if value is None else f"{value:.1f}",
                        "temperature_missing": int(value is None),
                        "quality_temperature": row["QN_9"].strip(),
                    }
                )
        geography = {}
        for name in archive.namelist():
            if name.startswith("Metadaten_Geographie_") and name.endswith(".txt"):
                with archive.open(name) as binary:
                    lines = binary.read().decode("latin-1").splitlines()
                for line in lines:
                    if line.strip().startswith("433;") and "20220913" in line:
                        parts = [item.strip() for item in line.split(";")]
                        geography = {
                            "station_id": parts[0],
                            "elevation_m": parts[1],
                            "latitude": parts[2],
                            "longitude": parts[3],
                            "valid_from": parts[4],
                            "valid_to": parts[5],
                            "station_name": parts[6],
                        }
                        break
        return rows, geography, member


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="DWD historical station ZIP archive")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO / "prototipo_3/data/de_alemania/berlin_temperature_2023",
    )
    args = parser.parse_args()
    source = args.source.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    rows, geography, member = extract(source)
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} hourly rows, got {len(rows)}")
    timestamps = [datetime.fromisoformat(row["timestamp_utc"]) for row in rows]
    if len(set(timestamps)) != len(timestamps):
        raise ValueError("DWD timestamps are duplicated")
    if any(right - left != __import__("datetime").timedelta(hours=1) for left, right in zip(timestamps, timestamps[1:])):
        raise ValueError("DWD UTC coverage is not continuous hourly")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "berlin_tempelhof_2023_hourly.csv"
    manifest_path = args.output_dir / "berlin_tempelhof_2023_manifest.json"
    fields = [
        "station_id", "timestamp_utc", "timestamp_local", "temperature_C",
        "temperature_missing", "quality_temperature",
    ]
    write_csv(output, rows, fields)
    source_hash = sha256(source)
    manifest = {
        "dataset": "berlin_tempelhof_temperature_2023",
        "source": {
            "archive": source.name,
            "path": str(source),
            "sha256": source_hash,
            "member": member,
            "catalog_url": "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/air_temperature/historical/",
            "description_url": "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/air_temperature/DESCRIPTION_obsgermany_climate_hourly_air_temperature_en.pdf",
        },
        "station": geography,
        "rules": {
            "period": "2023",
            "source_time_basis": "UTC according to DWD station metadata for 2001-04-01 onward",
            "output_timezone": "UTC plus Europe/Berlin presentation",
            "temperature_variable": "TT_TU",
            "unit": "degrees Celsius",
            "missing_value": "-999 converted to empty value and flagged",
            "imputation": False,
        },
        "coverage": {
            "rows": len(rows),
            "first_utc": rows[0]["timestamp_utc"],
            "last_utc": rows[-1]["timestamp_utc"],
            "missing_temperature_rows": sum(int(row["temperature_missing"]) for row in rows),
            "path": str(output.relative_to(REPO)),
            "sha256": sha256(output),
        },
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
