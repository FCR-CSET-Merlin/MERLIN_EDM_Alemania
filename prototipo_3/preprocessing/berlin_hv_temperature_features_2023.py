"""Join Berlin HV hourly demand and DWD temperature with causal lags."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[2]
LOCAL_TZ = ZoneInfo("Europe/Berlin")
UTC = timezone.utc


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("demand", type=Path, help="Berlin HV hourly CSV")
    parser.add_argument("temperature", type=Path, help="DWD hourly temperature CSV")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO / "prototipo_3/data/de_alemania/berlin_features_2023",
    )
    args = parser.parse_args()
    demand = read_csv(args.demand.resolve())
    temperature = read_csv(args.temperature.resolve())
    if len(demand) != 8760 or len(temperature) != 8760:
        raise ValueError(f"Expected 8760 rows in each input, got {len(demand)} and {len(temperature)}")

    demand_by_end = {parse_utc(row["timestamp_hour_end_utc"]): row for row in demand}
    temp_by_time: dict[datetime, float | None] = {}
    for row in temperature:
        stamp = parse_utc(row["timestamp_utc"])
        if stamp in temp_by_time:
            raise ValueError(f"Duplicate temperature timestamp {stamp}")
        temp_by_time[stamp] = None if row["temperature_C"] == "" else float(row["temperature_C"])

    rows: list[dict[str, object]] = []
    for timestamp in sorted(demand_by_end):
        demand_row = demand_by_end[timestamp]
        values: dict[str, float | None] = {}
        for lag in range(8):
            values[f"temperature_t_minus_{lag}_C"] = temp_by_time.get(timestamp - timedelta(hours=lag))
        missing = [value is None for value in values.values()]
        local = timestamp.astimezone(LOCAL_TZ)
        output: dict[str, object] = {
            "timestamp_hour_end_utc": timestamp.isoformat(),
            "timestamp_hour_end_local": local.isoformat(),
            "load_mean_MW": demand_row["load_mean_MW"],
            "energy_MWh": demand_row["energy_MWh"],
            "temperature_missing_any": int(any(missing)),
            "temperature_complete_8lags": int(not any(missing)),
            "hour_local": local.hour,
            "day_of_week_local": local.weekday(),
            "month_local": local.month,
            "day_of_year_local": local.timetuple().tm_yday,
            "is_weekend_local": int(local.weekday() >= 5),
        }
        for lag, value in values.items():
            output[lag] = "" if value is None else f"{value:.1f}"
        rows.append(output)

    if len(rows) != 8760:
        raise ValueError("Joined feature table is incomplete")
    complete = sum(int(row["temperature_complete_8lags"]) for row in rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "berlin_hv_temperature_features_2023.csv"
    manifest_path = args.output_dir / "berlin_hv_temperature_features_2023_manifest.json"
    fields = [
        "timestamp_hour_end_utc", "timestamp_hour_end_local", "load_mean_MW", "energy_MWh",
        *[f"temperature_t_minus_{lag}_C" for lag in range(8)],
        "temperature_missing_any", "temperature_complete_8lags", "hour_local",
        "day_of_week_local", "month_local", "day_of_year_local", "is_weekend_local",
    ]
    write_csv(output, rows, fields)
    manifest = {
        "dataset": "berlin_hv_temperature_features_2023",
        "join_key": "HV timestamp_hour_end_utc = DWD timestamp_utc",
        "demand_input": {"path": str(args.demand.resolve()), "sha256": sha256(args.demand.resolve())},
        "temperature_input": {"path": str(args.temperature.resolve()), "sha256": sha256(args.temperature.resolve())},
        "rules": {
            "temperature_lags": "current hour and 1 to 7 previous UTC hours",
            "timezone_presentation": "Europe/Berlin",
            "missing_temperature_imputation": False,
            "calendar_holidays": "not included yet; requires German holiday calendar decision",
        },
        "coverage": {
            "rows": len(rows),
            "complete_8lag_rows": complete,
            "excluded_if_complete_case": len(rows) - complete,
            "first_timestamp_hour_end_utc": rows[0]["timestamp_hour_end_utc"],
            "last_timestamp_hour_end_utc": rows[-1]["timestamp_hour_end_utc"],
            "path": str(output.relative_to(REPO)),
            "sha256": sha256(output),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
