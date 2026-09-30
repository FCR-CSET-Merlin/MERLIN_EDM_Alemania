"""Build German Parquet datasets under the Chilean 24-feature MLP contract.

The script does not reuse Chilean weights or scalers. It creates chronological
train/validation/test Parquet files from the Berlin d=8 common feature table,
with German calendar features and an explicit provisional sector mapping.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[2]
UTC = timezone.utc
BERLIN = ZoneInfo("Europe/Berlin")
CALENDAR_COLUMNS = [
    "hour_sin", "hour_cos", "dow_sin", "dow_cos", "doy_sin", "doy_cos",
    "is_working_day", "is_holiday", "is_weekend", "region_comuna_share",
    "share_I", "share_R", "share_C", "share_P", "share_T", "is_comuna",
]
TARGET_COLUMN = "target_scaled"

def feature_columns(dimension: int) -> list[str]:
    if dimension not in (3, 5, 8):
        raise ValueError("dimension must be 3, 5 or 8")
    return [*CALENDAR_COLUMNS, "temperatura", *[f"temp_t - {lag}" for lag in range(1, dimension)]]
SHARE_COLUMNS = ["share_I", "share_R", "share_C", "share_P", "share_T"]
SHARE_TEMPORAL_RESOLUTION = "annual_broadcast"
DEFAULT_INPUT = REPO / "prototipo_3/data/de_alemania/berlin_lag_ablation_2023/common_d3_d5_d8/d8/berlin_hv_temperature_d8_2023_common.csv"
DEFAULT_SHARES = REPO / "corfo-report/validation/berlin/berlin_sector_shares_2023.csv"
DEFAULT_OUTPUT = REPO / "prototipo_3/data/de_alemania/berlin_training_2023"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp without timezone: {value}")
    return parsed.astimezone(UTC)


def easter_sunday(year: int) -> date:
    # Anonymous Gregorian algorithm, sufficient for German public holidays.
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def berlin_holidays(year: int) -> set[date]:
    easter = easter_sunday(year)
    fixed = {
        date(year, 1, 1), date(year, 3, 8), date(year, 5, 1),
        date(year, 10, 3), date(year, 12, 25), date(year, 12, 26),
    }
    movable = {
        easter - timedelta(days=2),   # Good Friday
        easter + timedelta(days=1),   # Easter Monday
        easter + timedelta(days=39),  # Ascension Day
        easter + timedelta(days=50),  # Whit Monday
    }
    return fixed | movable


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_shares(path: Path) -> dict[str, object]:
    rows = read_rows(path)
    if len(rows) != 1:
        raise ValueError(f"Expected exactly one Berlin share row, got {len(rows)}")
    row = rows[0]
    required = {"territory", "year", "region_comuna_share", *SHARE_COLUMNS}
    missing = required.difference(row)
    if missing:
        raise ValueError(f"Missing share columns: {sorted(missing)}")
    values = {name: float(row[name]) for name in ["region_comuna_share", *SHARE_COLUMNS]}
    if not all(math.isfinite(value) for value in values.values()):
        raise ValueError("Shares contain non-finite values")
    if values["region_comuna_share"] < 0 or values["region_comuna_share"] > 1:
        raise ValueError("region_comuna_share must be in [0, 1]")
    if any(values[name] < 0 or values[name] > 1 for name in SHARE_COLUMNS):
        raise ValueError("Sector shares must be in [0, 1]")
    if not math.isclose(sum(values[name] for name in SHARE_COLUMNS), 1.0, abs_tol=1e-9):
        raise ValueError("Sector shares must sum to 1")
    return {
        "territory": row["territory"],
        "year": int(row["year"]),
        **values,
        "source": row.get("source", ""),
        "sector_mapping_policy": row.get("sector_mapping_policy", ""),
        "temporal_resolution": SHARE_TEMPORAL_RESOLUTION,
    }


def build_calendar(timestamp: datetime) -> dict[str, float | int]:
    local = timestamp.astimezone(BERLIN)
    day_of_year = local.timetuple().tm_yday
    days_in_year = 366 if (local.year % 4 == 0 and (local.year % 100 != 0 or local.year % 400 == 0)) else 365
    holiday = int(local.date() in berlin_holidays(local.year))
    weekend = int(local.weekday() >= 5)
    return {
        "hour_sin": math.sin(2 * math.pi * local.hour / 24),
        "hour_cos": math.cos(2 * math.pi * local.hour / 24),
        "dow_sin": math.sin(2 * math.pi * local.weekday() / 7),
        "dow_cos": math.cos(2 * math.pi * local.weekday() / 7),
        "doy_sin": math.sin(2 * math.pi * day_of_year / days_in_year),
        "doy_cos": math.cos(2 * math.pi * day_of_year / days_in_year),
        "is_working_day": int(not weekend and not holiday),
        "is_holiday": holiday,
        "is_weekend": weekend,
    }


def write_parquet(path: Path, rows: list[dict[str, float | int]], columns: list[str]) -> None:
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("This step requires pandas and pyarrow; install requirements.txt in the training environment") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows, columns=columns)
    frame.to_parquet(path, index=False, engine="pyarrow")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--dimension", type=int, choices=(3, 5, 8), default=8)
    parser.add_argument("--shares", type=Path, default=DEFAULT_SHARES)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    input_path = args.input.resolve()
    shares_path = args.shares.resolve()
    output_root = args.output_root.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    if not shares_path.is_file():
        raise FileNotFoundError(shares_path)
    if output_root.exists() and any(output_root.iterdir()) and not args.overwrite:
        raise FileExistsError(f"Output exists; use --overwrite: {output_root}")

    shares = read_shares(shares_path)
    input_rows = read_rows(input_path)
    if not input_rows:
        raise ValueError("Input feature table is empty")
    temp_input_columns = [f"temperature_t_minus_{i}_C" for i in range(args.dimension)]
    required_input = {"timestamp_hour_end_utc", "load_mean_MW", *temp_input_columns}
    missing = required_input.difference(input_rows[0])
    if missing:
        raise ValueError(f"Missing feature-table columns: {sorted(missing)}")

    parsed = []
    for row in input_rows:
        timestamp = parse_utc(row["timestamp_hour_end_utc"])
        load = float(row["load_mean_MW"])
        temperatures = [float(row[column]) for column in temp_input_columns]
        parsed.append((timestamp, load, temperatures))
    parsed.sort(key=lambda item: item[0])
    if len({item[0] for item in parsed}) != len(parsed):
        raise ValueError("Duplicate UTC timestamps")
    # The source is a 2023 UTC sequence indexed by hour end; its final
    # interval closes at 2024-01-01 local time. Validate the source period
    # with UTC years and use the local end timestamp for calendar features.
    utc_years = {item[0].year for item in parsed}
    if utc_years != {shares["year"]}:
        raise ValueError(f"Input UTC years {utc_years} do not match share year {shares['year']}")

    n = len(parsed)
    train_end = max(1, int(math.floor(n * 0.70)))
    val_end = max(train_end + 1, int(math.floor(n * 0.85)))
    train_values = [item[1] for item in parsed[:train_end]]
    mu = sum(train_values) / len(train_values)
    variance = sum((value - mu) ** 2 for value in train_values) / max(1, len(train_values) - 1)
    sigma = math.sqrt(variance)
    if not math.isfinite(sigma) or sigma <= 0:
        raise ValueError("Training target standard deviation must be positive")

    all_rows = []
    for timestamp, load, temperatures in parsed:
        calendar = build_calendar(timestamp)
        row: dict[str, float | int] = {**calendar}
        row["region_comuna_share"] = shares["region_comuna_share"]
        row.update({name: shares[name] for name in SHARE_COLUMNS})
        row["is_comuna"] = 0
        row["temperatura"] = temperatures[0]
        for lag in range(1, args.dimension):
            row[f"temp_t - {lag}"] = temperatures[lag]
        row[TARGET_COLUMN] = (load - mu) / sigma
        all_rows.append(row)

    split_rows = {
        "train": all_rows[:train_end],
        "validation": all_rows[train_end:val_end],
        "test": all_rows[val_end:],
    }
    output_root.mkdir(parents=True, exist_ok=True)
    outputs = {}
    model_features = feature_columns(args.dimension)
    for split, rows in split_rows.items():
        path = output_root / f"berlin_2023_d{args.dimension}_{split}.parquet"
        write_parquet(path, rows, [*model_features, TARGET_COLUMN])
        outputs[split] = {"path": str(path.relative_to(REPO)), "rows": len(rows), "sha256": sha256(path)}

    manifest = {
        "dataset": "berlin_training_contract_2023",
        "status": "provisional_contract_ready_for_german_retraining",
        "input": {"path": str(input_path.relative_to(REPO)), "sha256": sha256(input_path), "rows": n},
        "shares": {"path": str(shares_path.relative_to(REPO)), "sha256": sha256(shares_path), **shares},
        "sector_share_temporal_resolution": SHARE_TEMPORAL_RESOLUTION,
        "dimension": args.dimension,
        "tau_hours": 1,
        "features": model_features,
        "target": TARGET_COLUMN,
        "target_definition": "(load_mean_MW - mu_train_MW) / sigma_train_MW",
        "scaling": {"mu_train_MW": mu, "sigma_train_MW": sigma, "fit_rows": train_end, "fit_policy": "chronological train partition only"},
        "split": {"train_rows": train_end, "validation_rows": val_end - train_end, "test_rows": n - val_end, "train_fraction": 0.70, "validation_fraction": 0.15, "test_fraction": 0.15},
        "calendar": {"timezone": "Europe/Berlin", "holiday_policy": "Berlin public holidays; includes International Women's Day (8 March)"},
        "spatial": {"territory": shares["territory"], "is_comuna": 0, "region_comuna_share_interpretation": "provisional pilot-relative share; 1.0 is not a Germany-national fraction"},
        "sector_mapping": shares["sector_mapping_policy"],
        "outputs": outputs,
        "chilean_weights": "not used",
    }
    manifest_path = output_root / f"berlin_training_contract_d{args.dimension}_2023_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
