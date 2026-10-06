"""Audit the multiyear Berlin Parquet contracts without retraining."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DIMENSIONS = (3, 5, 8)
SPLITS = ("train", "validation", "test")
YEARS = {"train": (2020, 2021, 2022), "validation": (2023,), "test": (2024,)}
SHARE_COLUMNS = ("region_comuna_share", "share_I", "share_R", "share_C", "share_P", "share_T")
DEFAULT_CONTRACT_ROOT = REPO / "prototipo_3/data/de_alemania/berlin_training_multiyear"
DEFAULT_SHARES = REPO / "corfo-report/validation/berlin/berlin_sector_shares_multiyear_2020_2024.csv"
DEFAULT_REPORT_ROOT = REPO / "corfo-report/validation/berlin/multiyear_2020_2024"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract-root", type=Path, default=DEFAULT_CONTRACT_ROOT)
    parser.add_argument("--shares", type=Path, default=DEFAULT_SHARES)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    args = parser.parse_args()
    try:
        import numpy as np
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("The contract audit requires numpy, pandas and pyarrow") from exc

    root = args.contract_root.resolve()
    shares_path = args.shares.resolve()
    report_root = args.report_root.resolve()
    shares_rows = read_csv(shares_path)
    allowed = {
        year: {column: float(row[column]) for column in SHARE_COLUMNS}
        for year, row in ((int(row["year"]), row) for row in shares_rows)
    }
    records: list[dict[str, object]] = []
    for dimension in DIMENSIONS:
        manifest_path = root / f"berlin_training_contract_multiyear_d{dimension}_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        features = manifest["features"]
        expected_columns = [*features, "target_scaled"]
        for split in SPLITS:
            path = root / f"berlin_multiyear_d{dimension}_{split}.parquet"
            frame = pd.read_parquet(path, engine="pyarrow")
            column_ok = list(frame.columns) == expected_columns
            finite_ok = bool(np.isfinite(frame.to_numpy(dtype=float)).all())
            share_sum = frame[[f"share_{code}" for code in "IR CPT".replace(" ", "")]].sum(axis=1)
            share_sum_error = float(np.max(np.abs(share_sum - 1.0)))
            shares_ok = True
            max_share_error = 0.0
            for column in SHARE_COLUMNS:
                expected_values = [allowed[year][column] for year in YEARS[split]]
                observed = frame[column].to_numpy(dtype=float)
                for value in observed:
                    error = min(abs(float(value) - expected) for expected in expected_values)
                    max_share_error = max(max_share_error, error)
                    shares_ok = shares_ok and error <= 1e-10
            target_mean = float(frame["target_scaled"].mean())
            target_finite = bool(np.isfinite(frame["target_scaled"].to_numpy(dtype=float)).all())
            train_mean_ok = split != "train" or abs(target_mean) <= 1e-10
            status = bool(column_ok and finite_ok and shares_ok and share_sum_error <= 1e-10 and target_finite and train_mean_ok)
            records.append({
                "dimension": dimension,
                "split": split,
                "years": ",".join(map(str, YEARS[split])),
                "rows": len(frame),
                "columns_ok": column_ok,
                "finite_ok": finite_ok,
                "shares_allowed_ok": shares_ok,
                "share_sum_max_abs_error": f"{share_sum_error:.3e}",
                "share_max_abs_error": f"{max_share_error:.3e}",
                "target_mean_scaled": f"{target_mean:.12g}",
                "target_finite": target_finite,
                "train_target_mean_ok": train_mean_ok,
                "status": "pass" if status else "fail",
            })

    report_root.mkdir(parents=True, exist_ok=True)
    csv_path = report_root / "berlin_multiyear_contract_audit.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    passed = all(row["status"] == "pass" for row in records)
    md_path = report_root / "berlin_multiyear_contract_audit.md"
    lines = [
        "# Auditoría del contrato Berlín multianual",
        "",
        f"Estado global: **{'PASS' if passed else 'FAIL'}**.",
        "",
        "Se verificaron columnas, valores finitos, suma de shares, correspondencia con los shares anuales permitidos y objetivo escalado. La partición se mantiene por años completos y el holdout 2024 usa la fila marcada como carry-forward 2023.",
        "",
        "| d | Partición | Filas | Columnas | Finitud | Shares | Error suma | Media target train | Estado |",
        "|---:|---|---:|:---:|:---:|:---:|---:|---:|:---:|",
    ]
    for row in records:
        lines.append(
            f"| {row['dimension']} | {row['split']} | {row['rows']} | {row['columns_ok']} | {row['finite_ok']} | {row['shares_allowed_ok']} | {row['share_sum_max_abs_error']} | {row['target_mean_scaled']} | {row['status']} |"
        )
    lines.extend([
        "",
        "El resultado no evalúa el MAPE: solo acredita la integridad del contrato antes del reentrenamiento.",
    ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "pass" if passed else "fail", "audit": str(md_path), "rows": records}, ensure_ascii=False, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
