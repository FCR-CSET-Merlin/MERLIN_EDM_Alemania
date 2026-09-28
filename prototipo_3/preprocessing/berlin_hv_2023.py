"""Prepare the Stromnetz Berlin HV 2023 profile for the German pilot.

The source labels are preserved verbatim. A UTC sequence is generated from the
published first quarter-hour and the values are aggregated in consecutive
four-quarter blocks. The operator has not yet confirmed whether timestamps are
interval starts or ends, so the output exposes both quarter-hour labels and
explicit hour-start/hour-end fields instead of silently changing the source.

This implementation uses only the Python standard library so that the data
contract can be audited before installing the full model environment.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[2]
LOCAL_TZ = ZoneInfo("Europe/Berlin")
UTC = timezone.utc
SOURCE_URL = (
    "https://www.stromnetz.berlin/files/globalassets/dokumente/"
    "veroffentlichungspflichten/2023/Jahreshoechstlast-2023-Hochspannung.csv"
)
DATE_RE = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")
TIME_RE = re.compile(r"^\d{2}:\d{2}$")
EXPECTED_ROWS = 365 * 96


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_power(value: str) -> int:
    cleaned = value.strip().replace(".", "").replace(",", ".")
    return int(round(float(cleaned)))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_source(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for source_row, row in enumerate(csv.reader(handle, delimiter=";"), start=1):
            if len(row) < 3:
                continue
            date_text, time_text, power_text = (cell.strip() for cell in row[:3])
            if not DATE_RE.fullmatch(date_text) or not TIME_RE.fullmatch(time_text):
                continue
            rows.append(
                {
                    "source_row": source_row,
                    "published_timestamp_local": f"{date_text} {time_text}",
                    "published_datetime": datetime.strptime(
                        f"{date_text} {time_text}", "%d.%m.%Y %H:%M"
                    ),
                    "Wert_kW": parse_power(power_text),
                }
            )
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} quarter-hours, got {len(rows)}")
    return rows


def normalize_quarter_hours(rows: list[dict[str, object]], year: int) -> list[dict[str, object]]:
    first_local = datetime(year, 1, 1, 0, 15, tzinfo=LOCAL_TZ)
    first_utc = first_local.astimezone(UTC)
    result: list[dict[str, object]] = []
    for position, source in enumerate(rows):
        timestamp_utc = first_utc + timedelta(minutes=15 * position)
        timestamp_local = timestamp_utc.astimezone(LOCAL_TZ)
        published = source["published_datetime"]
        mismatch = published != timestamp_local.replace(tzinfo=None)
        result.append(
            {
                "source_row": source["source_row"],
                "sequence_position": position,
                "published_timestamp_local": source["published_timestamp_local"],
                "timestamp_utc": timestamp_utc.isoformat(),
                "timestamp_local_normalized": timestamp_local.isoformat(),
                "timestamp_label_mismatch": int(mismatch),
                "Wert_kW": source["Wert_kW"],
                "energy_qh_kWh": f"{float(source['Wert_kW']) * 0.25:.6f}",
                "hour_group": position // 4,
            }
        )
    for previous, current in zip(result, result[1:]):
        left = datetime.fromisoformat(previous["timestamp_utc"])
        right = datetime.fromisoformat(current["timestamp_utc"])
        if right - left != timedelta(minutes=15):
            raise ValueError("Generated UTC index is not strictly quarter-hourly")
    return result


def aggregate_hours(quarter_hours: list[dict[str, object]]) -> list[dict[str, object]]:
    hourly: list[dict[str, object]] = []
    for group_start in range(0, len(quarter_hours), 4):
        group = quarter_hours[group_start:group_start + 4]
        if len(group) != 4:
            raise ValueError("Hourly aggregation contains an incomplete block")
        first = datetime.fromisoformat(group[0]["timestamp_utc"])
        last = datetime.fromisoformat(group[-1]["timestamp_utc"])
        powers = [int(item["Wert_kW"]) for item in group]
        energy_mwh = sum(powers) * 0.25 / 1000
        hourly.append(
            {
                "hour_group": int(group[0]["hour_group"]),
                "timestamp_hour_start_utc": (first - timedelta(minutes=15)).isoformat(),
                "timestamp_hour_end_utc": last.isoformat(),
                "timestamp_hour_start_local": (first - timedelta(minutes=15)).astimezone(LOCAL_TZ).isoformat(),
                "timestamp_hour_end_local": last.astimezone(LOCAL_TZ).isoformat(),
                "quarter_hours": 4,
                "load_mean_kW": f"{sum(powers) / 4:.6f}",
                "load_mean_MW": f"{sum(powers) / 4 / 1000:.9f}",
                "energy_MWh": f"{energy_mwh:.9f}",
                "source_row_start": int(group[0]["source_row"]),
                "source_row_end": int(group[-1]["source_row"]),
                "published_timestamp_mismatch_count": sum(
                    int(item["timestamp_label_mismatch"]) for item in group
                ),
            }
        )
    if len(hourly) != 365 * 24:
        raise ValueError(f"Expected 8760 hourly rows, got {len(hourly)}")
    return hourly


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Downloaded Stromnetz Berlin HV 2023 CSV")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO / "prototipo_3/data/de_alemania/berlin_hv_2023",
    )
    parser.add_argument(
        "--report-index",
        type=Path,
        default=REPO / "corfo-report/results/timeseries/berlin_hv_2023_index.csv",
    )
    args = parser.parse_args()
    source = args.source.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    quarter_hours = normalize_quarter_hours(read_source(source), 2023)
    hourly = aggregate_hours(quarter_hours)

    qh_fields = [
        "source_row", "sequence_position", "published_timestamp_local", "timestamp_utc",
        "timestamp_local_normalized", "timestamp_label_mismatch", "Wert_kW",
        "energy_qh_kWh", "hour_group",
    ]
    hourly_fields = [
        "hour_group", "timestamp_hour_start_utc", "timestamp_hour_end_utc",
        "timestamp_hour_start_local", "timestamp_hour_end_local", "quarter_hours",
        "load_mean_kW", "load_mean_MW", "energy_MWh", "source_row_start",
        "source_row_end", "published_timestamp_mismatch_count",
    ]
    quarter_path = args.output_dir / "berlin_hv_2023_15min_normalized.csv"
    hourly_path = args.output_dir / "berlin_hv_2023_hourly.csv"
    manifest_path = args.output_dir / "berlin_hv_2023_manifest.json"
    write_csv(quarter_path, quarter_hours, qh_fields)
    write_csv(hourly_path, hourly, hourly_fields)

    source_hash = sha256(source)
    manifest = {
        "dataset": "berlin_hv_2023",
        "source": {"url": SOURCE_URL, "path": str(source), "sha256": source_hash},
        "rules": {
            "local_timezone": "Europe/Berlin",
            "first_published_timestamp": "2023-01-01 00:15",
            "generated_index": "first local timestamp converted to UTC, then +15 minutes by row",
            "hourly_aggregation": "four consecutive quarter-hour rows; mean power and sum of kWh",
            "raw_labels_preserved": True,
            "operator_semantics_confirmed": False,
        },
        "quarter_hour": {
            "rows": len(quarter_hours),
            "first_utc": quarter_hours[0]["timestamp_utc"],
            "last_utc": quarter_hours[-1]["timestamp_utc"],
            "label_mismatches": sum(int(row["timestamp_label_mismatch"]) for row in quarter_hours),
            "path": str(quarter_path.relative_to(REPO)),
            "sha256": sha256(quarter_path),
        },
        "hourly": {
            "rows": len(hourly),
            "first_hour_start_utc": hourly[0]["timestamp_hour_start_utc"],
            "last_hour_end_utc": hourly[-1]["timestamp_hour_end_utc"],
            "energy_MWh": round(sum(float(row["energy_MWh"]) for row in hourly), 6),
            "path": str(hourly_path.relative_to(REPO)),
            "sha256": sha256(hourly_path),
        },
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    index_rows = [
        {
            "dataset": "berlin_hv_2023_quarter_hourly",
            "period": "2023",
            "rows": len(quarter_hours),
            "frequency": "15min",
            "value_column": "Wert_kW",
            "energy_column": "energy_qh_kWh",
            "timezone": "UTC index; Europe/Berlin presentation",
            "territory": "Berlin-administrative / Stromnetz-Berlin-HV-area-proxy",
            "source_url": SOURCE_URL,
            "source_sha256": source_hash,
            "artifact": str(quarter_path.relative_to(REPO)),
            "artifact_sha256": sha256(quarter_path),
            "status": "ready_for_model_input_after_operator_semantics_check",
        },
        {
            "dataset": "berlin_hv_2023_hourly",
            "period": "2023",
            "rows": len(hourly),
            "frequency": "1h",
            "value_column": "load_mean_MW",
            "energy_column": "energy_MWh",
            "timezone": "UTC hour start/end; Europe/Berlin presentation",
            "territory": "Berlin-administrative / Stromnetz-Berlin-HV-area-proxy",
            "source_url": SOURCE_URL,
            "source_sha256": source_hash,
            "artifact": str(hourly_path.relative_to(REPO)),
            "artifact_sha256": sha256(hourly_path),
            "status": "ready_for_model_input_after_operator_semantics_check",
        },
    ]
    write_csv(args.report_index, index_rows, list(index_rows[0]))
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
