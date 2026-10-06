"""Build chronological d=3, d=5 and d=8 Parquet contracts for Berlin.

The temporal experiment is deliberately separated from the 2023 pilot:
training uses complete rows from 2020-2022, validation is the full 2023
calendar and the frozen holdout is 2024. The scaler is fitted only on the
training years. Shares are annual and year-specific for 2020-2023; 2024 uses
the explicitly labelled last-available 2023 row only for holdout inference.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
UTC = timezone.utc
DIMENSIONS = (3, 5, 8)
SHARE_COLUMNS = ("region_comuna_share", "share_I", "share_R", "share_C", "share_P", "share_T")
DEFAULT_FEATURES = REPO / "prototipo_3/data/de_alemania/berlin_multiyear/berlin_hv_temperature_features_2020_2024.csv"
DEFAULT_SHARES = REPO / "corfo-report/validation/berlin/berlin_sector_shares_multiyear_2020_2024.csv"
DEFAULT_OUTPUT = REPO / "prototipo_3/data/de_alemania/berlin_training_multiyear"
DEFAULT_REPORT = REPO / "corfo-report/validation/berlin/multiyear_2020_2024"
SPLITS = {"train": {2020, 2021, 2022}, "validation": {2023}, "test": {2024}}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_contract_module():
    path = REPO / "prototipo_3/preprocessing/berlin_training_contract_2023.py"
    spec = importlib.util.spec_from_file_location("berlin_training_contract_2023", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_shares(path: Path) -> dict[int, dict[str, object]]:
    rows = read_csv(path)
    shares: dict[int, dict[str, object]] = {}
    for row in rows:
        year = int(row["year"])
        if year in shares:
            raise ValueError(f"Duplicate share year {year}")
        values = {column: float(row[column]) for column in SHARE_COLUMNS}
        if not math.isclose(sum(values[column] for column in SHARE_COLUMNS[1:]), 1.0, abs_tol=1e-9):
            raise ValueError(f"Shares do not sum to one for {year}")
        shares[year] = {
            **values,
            "source_year": int(row["source_year"]),
            "share_status": row["share_status"],
            "source": row["source"],
        }
    required = set().union(*SPLITS.values())
    missing = required.difference(shares)
    if missing:
        raise ValueError(f"Missing annual shares for {sorted(missing)}")
    return shares


def parse_utc(value: str) -> datetime:
    stamp = datetime.fromisoformat(value)
    if stamp.tzinfo is None:
        raise ValueError(f"Timestamp without timezone: {value}")
    return stamp.astimezone(UTC)


def target_scale(values: list[float]) -> tuple[float, float]:
    mu = sum(values) / len(values)
    variance = sum((value - mu) ** 2 for value in values) / max(1, len(values) - 1)
    sigma = math.sqrt(variance)
    if not math.isfinite(sigma) or sigma <= 0:
        raise ValueError("Training target standard deviation must be positive")
    return mu, sigma


def write_parquet(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("This step requires pandas and pyarrow") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=columns).to_parquet(path, index=False, engine="pyarrow")


def build_rows(feature_rows: list[dict[str, str]], shares: dict[int, dict[str, object]], dimension: int, contract: object) -> list[dict[str, object]]:
    rows = []
    seen: set[datetime] = set()
    temp_columns = [f"temperature_t_minus_{lag}_C" for lag in range(dimension)]
    for source in feature_rows:
        year = int(source["source_year"])
        if year not in shares:
            continue
        timestamp = parse_utc(source["timestamp_hour_end_utc"])
        if timestamp in seen:
            raise ValueError(f"Duplicate UTC timestamp in d={dimension}: {timestamp}")
        values = [source[column] for column in temp_columns]
        if any(value == "" for value in values):
            continue
        calendar = contract.build_calendar(timestamp)
        row: dict[str, object] = {**calendar, **{column: shares[year][column] for column in SHARE_COLUMNS}}
        row["is_comuna"] = 0
        row["temperatura"] = float(values[0])
        for lag in range(1, dimension):
            row[f"temp_t - {lag}"] = float(values[lag])
        row["_year"] = year
        row["_timestamp"] = timestamp
        row["_load_MW"] = float(source["load_mean_MW"])
        rows.append(row)
        seen.add(timestamp)
    return sorted(rows, key=lambda row: row["_timestamp"])


def split_rows(rows: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    result = {name: [] for name in SPLITS}
    for row in rows:
        for split, years in SPLITS.items():
            if row["_year"] in years:
                result[split].append(row)
                break
        else:
            raise ValueError(f"Year outside split map: {row['_year']}")
    for split in result:
        result[split].sort(key=lambda row: row["_timestamp"])
        if not result[split]:
            raise ValueError(f"Empty split: {split}")
    return result


def strip_private(row: dict[str, object], features: list[str], target: str, mu: float, sigma: float) -> dict[str, object]:
    result = {feature: row[feature] for feature in features}
    result[target] = (float(row["_load_MW"]) - mu) / sigma
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--shares", type=Path, default=DEFAULT_SHARES)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    features_path = args.features.resolve()
    shares_path = args.shares.resolve()
    output_root = args.output_root.resolve()
    report_root = args.report_root.resolve()
    if not features_path.is_file():
        raise FileNotFoundError(features_path)
    if not shares_path.is_file():
        raise FileNotFoundError(shares_path)
    if output_root.exists() and any(output_root.iterdir()) and not args.overwrite:
        raise FileExistsError(f"Output exists; use --overwrite: {output_root}")

    contract = load_contract_module()
    feature_rows = read_csv(features_path)
    shares = read_shares(shares_path)
    manifests = []
    report_rows = []
    for dimension in DIMENSIONS:
        rows = build_rows(feature_rows, shares, dimension, contract)
        partitions = split_rows(rows)
        train_values = [float(row["_load_MW"]) for row in partitions["train"]]
        mu, sigma = target_scale(train_values)
        features = contract.feature_columns(dimension)
        outputs = {}
        for split, partition in partitions.items():
            path = output_root / f"berlin_multiyear_d{dimension}_{split}.parquet"
            clean = [strip_private(row, features, "target_scaled", mu, sigma) for row in partition]
            write_parquet(path, clean, [*features, "target_scaled"])
            outputs[split] = {"path": str(path.relative_to(REPO)), "rows": len(clean), "sha256": sha256(path)}
            report_rows.append({
                "dimension": dimension,
                "split": split,
                "rows": len(clean),
                "years": ",".join(map(str, sorted(SPLITS[split]))),
                "mu_train_MW": f"{mu:.12f}",
                "sigma_train_MW": f"{sigma:.12f}",
                "output": str(path.relative_to(REPO)),
            })
        manifest = {
            "dataset": "berlin_training_contract_multiyear_2020_2024",
            "status": "chronological_contract_ready_for_multiyear_retraining",
            "dimension": dimension,
            "tau_hours": 1,
            "features": features,
            "target": "target_scaled",
            "inputs": {
                "features": {"path": str(features_path.relative_to(REPO)), "sha256": sha256(features_path)},
                "shares": {"path": str(shares_path.relative_to(REPO)), "sha256": sha256(shares_path), "temporal_resolution": "annual_broadcast"},
            },
            "split": {
                "train_years": sorted(SPLITS["train"]),
                "validation_years": sorted(SPLITS["validation"]),
                "test_years": sorted(SPLITS["test"]),
                "policy": "complete chronological years; no row redistribution between partitions",
            },
            "scaling": {
                "mu_train_MW": mu,
                "sigma_train_MW": sigma,
                "fit_policy": "training years 2020-2022 only",
            },
            "shuffle": {
                "partition_policy": "chronological by year",
                "training_batch_policy": "trainer default may shuffle within training partition only",
                "validation_test_shuffle": False,
            },
            "shares": {
                "annual_by_year": {
                    str(year): {
                        "source_year": shares[year]["source_year"],
                        "share_status": shares[year]["share_status"],
                        **{column: shares[year][column] for column in SHARE_COLUMNS},
                    }
                    for year in sorted(shares)
                },
                "holdout_2024_carry_forward": True,
            },
            "outputs": outputs,
            "chilean_weights": "not used",
        }
        manifest_path = output_root / f"berlin_training_contract_multiyear_d{dimension}_manifest.json"
        output_root.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifests.append(manifest)

    report_root.mkdir(parents=True, exist_ok=True)
    report_csv = report_root / "berlin_multiyear_contract_index.csv"
    with report_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(report_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(report_rows)
    report_md = report_root / "berlin_multiyear_contract.md"
    report_md.write_text(
        "# Contrato de entrenamiento Berlín multianual 2020-2024\n\n"
        "Se generaron contratos independientes para d=3, d=5 y d=8. La partición es cronológica por año: entrenamiento 2020-2022, validación 2023 y prueba/holdout 2024. El scaler se ajustó únicamente con el entrenamiento. Los shares son anuales; la fila 2024 está etiquetada como carry-forward 2023 para holdout.\n\n"
        + "| d | Partición | Años | Filas | mu train (MW) | sigma train (MW) |\n|---:|---|---|---:|---:|---:|\n"
        + "".join(
            f"| {row['dimension']} | {row['split']} | {row['years']} | {row['rows']} | {row['mu_train_MW']} | {row['sigma_train_MW']} |\n"
            for row in report_rows
        )
        + "\nLos Parquet están bajo prototipo_3/data y permanecen fuera de Git por su regla de exclusión. Antes de entrenar se debe ejecutar la auditoría de columnas, shares y cobertura, y mantener 2024 congelado como holdout.\n",
        encoding="utf-8",
    )
    print(json.dumps({"contracts": [m["dimension"] for m in manifests], "report": str(report_md), "rows": report_rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
