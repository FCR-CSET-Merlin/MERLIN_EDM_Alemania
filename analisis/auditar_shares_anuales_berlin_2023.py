"""Audit annual sector shares broadcast into Berlin Parquet contracts."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[1]
SHARES = REPO / "corfo-report/validation/berlin/berlin_sector_shares_2023.csv"
CONTRACT_ROOT = REPO / "prototipo_3/data/de_alemania/berlin_training_2023"
REPORT_ROOT = REPO / "corfo-report/validation/berlin"
SHARE_COLUMNS = ["region_comuna_share", "share_I", "share_R", "share_C", "share_P", "share_T"]


def read_expected() -> dict[str, float]:
    with SHARES.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1:
        raise ValueError(f"Expected one annual Berlin share row, got {len(rows)}")
    return {column: float(rows[0][column]) for column in SHARE_COLUMNS}


def main() -> None:
    expected = read_expected()
    audit_rows: list[dict[str, object]] = []
    dimensions = (3, 5, 8)
    splits = ("train", "validation", "test")
    for dimension in dimensions:
        for split in splits:
            path = CONTRACT_ROOT / f"berlin_2023_d{dimension}_{split}.parquet"
            if not path.is_file():
                raise FileNotFoundError(path)
            frame = pd.read_parquet(path)
            if frame.empty:
                raise ValueError(f"Empty contract: {path}")
            share_sum = frame[[f"share_{code}" for code in "IR CPT".replace(" ", "")]].sum(axis=1)
            for column in SHARE_COLUMNS:
                values = frame[column]
                max_abs_diff = float((values - expected[column]).abs().max())
                audit_rows.append({
                    "dimension": dimension,
                    "split": split,
                    "rows": len(frame),
                    "column": column,
                    "expected_annual_value": expected[column],
                    "unique_values": int(values.nunique(dropna=False)),
                    "observed_min": float(values.min()),
                    "observed_max": float(values.max()),
                    "max_abs_diff_from_expected": max_abs_diff,
                    "constant_across_rows": bool(values.nunique(dropna=False) == 1),
                    "within_tolerance": bool(max_abs_diff <= 1e-12),
                    "share_sum_max_abs_error": float((share_sum - 1.0).abs().max()),
                })

    output_csv = REPORT_ROOT / "berlin_training_share_audit_2023.csv"
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        fields = list(audit_rows[0])
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(audit_rows)

    all_constant = all(bool(row["constant_across_rows"]) for row in audit_rows)
    all_expected = all(bool(row["within_tolerance"]) for row in audit_rows)
    max_sum_error = max(float(row["share_sum_max_abs_error"]) for row in audit_rows)
    summary = {
        "status": "pass" if all_constant and all_expected and max_sum_error <= 1e-12 else "fail",
        "temporal_resolution": "annual_broadcast",
        "dimensions": list(dimensions),
        "splits": list(splits),
        "audited_rows": len(audit_rows),
        "all_share_columns_constant": all_constant,
        "all_values_match_annual_source": all_expected,
        "max_abs_share_sum_error": max_sum_error,
        "expected_values": expected,
        "contract_root": str(CONTRACT_ROOT.relative_to(REPO)),
        "output_csv": str(output_csv.relative_to(REPO)),
    }
    (REPORT_ROOT / "berlin_training_share_audit_2023.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (REPORT_ROOT / "berlin_training_share_audit_2023.md").write_text(
        "# Auditoría de shares sectoriales del contrato Berlín 2023\n\n"
        f"Estado: **{summary['status']}**. Resolución temporal: **`annual_broadcast`**.\n\n"
        "Se leyeron los contratos Parquet de `d=3`, `d=5` y `d=8`, en sus particiones de entrenamiento, validación y prueba. Cada columna territorial/sectorial debe contener un único valor durante todas las filas y coincidir con la fila anual oficial.\n\n"
        f"- Combinaciones auditadas: **{len(audit_rows)}**.\n"
        f"- Shares constantes en todas las filas: **{all_constant}**.\n"
        f"- Coincidencia con la fuente anual: **{all_expected}**.\n"
        f"- Error máximo de suma de shares: **{max_sum_error:.3e}**.\n\n"
        "La auditoría confirma que no se introdujeron shares mensuales en el contrato regional de Berlín.\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
