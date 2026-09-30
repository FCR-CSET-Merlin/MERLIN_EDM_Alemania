"""Build and audit the Berlin 2023 district-sector proxy matrix.

This runner uses only the Python standard library so the audit can be executed
without installing the modelling environment. It keeps the same policy as the
Pandas implementation: district weights come from Umweltatlas ``j2023g``,
sector totals from Strombilanz, and the detailed categories are proxies that
are reconciled by iterative proportional fitting.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DETAIL = REPO / "corfo-report/validation/berlin/external_2023/berlin_umweltatlas_bezirke_detail_2023.csv"
DISTRICTS = REPO / "corfo-report/validation/berlin/external_2023/berlin_umweltatlas_bezirke_2023.csv"
SECTORS = REPO / "corfo-report/validation/berlin/berlin_sector_shares_2023.csv"
BALANCE = REPO / "corfo-report/validation/berlin/external_2023/berlin_strombilanz_2023_extracted.csv"
OUT = REPO / "corfo-report/validation/berlin"
SECTOR_CODES = ("I", "R", "C", "P", "T")
SOURCE_COLUMNS = ("verbr_gewerbe", "verbr_haushalt", "verbr_nachtspeicher", "verbr_waermepumpe", "verbr_lastgangkunde")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ipf(seed: dict[str, dict[str, float]], row_targets: dict[str, float], column_targets: dict[str, float]) -> dict[str, dict[str, float]]:
    columns = list(column_targets)
    matrix = {row: {col: float(seed[row][col]) for col in columns} for row in seed}
    for _ in range(10000):
        for row, target in row_targets.items():
            total = sum(matrix[row].values())
            if total <= 0 and target > 1e-9:
                raise ValueError(f"Positive row target with zero seed: {row}")
            factor = target / total if total > 0 else 1.0
            for col in columns:
                matrix[row][col] *= factor
        for col, target in column_targets.items():
            total = sum(matrix[row][col] for row in matrix)
            if total <= 0 and target > 1e-9:
                raise ValueError(f"Positive column target with zero seed: {col}")
            factor = target / total if total > 0 else 1.0
            for row in matrix:
                matrix[row][col] *= factor
        row_error = max(abs(sum(matrix[row].values()) - row_targets[row]) for row in matrix)
        col_error = max(abs(sum(matrix[row][col] for row in matrix) - column_targets[col]) for col in columns)
        if max(row_error, col_error) <= 1e-9:
            return matrix
    raise RuntimeError("IPF did not converge")


def main() -> None:
    detail = read_csv(DETAIL)
    districts = read_csv(DISTRICTS)
    sector_shares = read_csv(SECTORS)
    balance = read_csv(BALANCE)
    if len(detail) != 12 or len(districts) != 12 or len(sector_shares) != 1:
        raise ValueError("Expected 12 districts and one Berlin sector-share row")
    district_by_id = {row["id_bezirk"]: row for row in districts}
    if set(district_by_id) != {row["id_bezirk"] for row in detail}:
        raise ValueError("District identifiers differ between Umweltatlas files")
    for row in detail:
        for column in SOURCE_COLUMNS:
            value = float(row[column])
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"Invalid proxy value {row['id_bezirk']}:{column}")

    categories = {row["category"]: float(row["value_gwh"]) for row in balance}
    targets = {
        "I": categories["industria_mineria"],
        "R": categories["hogares"],
        "C": categories["ghd_otros"],
        "P": 0.0,
        "T": categories["transporte"],
    }
    target_total = sum(targets.values())
    detail_total = sum(float(row["detail_total_gwh"]) for row in detail)
    spatial_total = sum(float(row["j2023g_gwh"]) for row in districts)
    ict_total = sum(targets[col] for col in ("I", "C", "T"))

    for row in detail:
        district = district_by_id[row["id_bezirk"]]
        row["bezirk"] = district["bezirk"]
        row["j2023g_gwh"] = float(district["j2023g_gwh"])
        row["district_weight"] = row["j2023g_gwh"] / spatial_total
        row["target_total_gwh"] = row["district_weight"] * target_total
        for col in SOURCE_COLUMNS + ("detail_total_gwh",):
            row[col] = float(row[col])
        row["seed_R"] = row["verbr_haushalt"] + row["verbr_nachtspeicher"] + row["verbr_waermepumpe"]
        row["seed_C"] = row["verbr_gewerbe"]
        for code in ("I", "C", "T"):
            row[f"seed_{code}"] = row["verbr_lastgangkunde"] * targets[code] / ict_total
        row["seed_P"] = 0.0
        row["seed_total_gwh"] = sum(row[f"seed_{code}"] for code in SECTOR_CODES)

    seed = {row["id_bezirk"]: {code: row[f"seed_{code}"] for code in SECTOR_CODES} for row in detail}
    row_targets = {row["id_bezirk"]: row["target_total_gwh"] for row in detail}
    fitted = ipf(seed, row_targets, targets)
    for row in detail:
        for code in SECTOR_CODES:
            row[f"raked_{code}"] = fitted[row["id_bezirk"]][code]
        row["raked_total_gwh"] = sum(row[f"raked_{code}"] for code in SECTOR_CODES)
        for code in SECTOR_CODES:
            row[f"share_{code}"] = row[f"raked_{code}"] / row["raked_total_gwh"]
        row["mapping_policy"] = "Haushalt+Nachtspeicher+Wärmepumpe->R; Gewerbe->C; Lastgangkunde split I/C/T by Strombilanz prior; IPF to totals"
        row["public_flag"] = "P target zero: public not separable in Strombilanz input"
        row["transport_flag"] = "T spatial proxy inherited from Lastgangkunde prior"
        row["monthly_data_flag"] = "annual_only; monthly profile pending"
        row["imputation_flag"] = "proxy_and_raked"

    OUT.mkdir(parents=True, exist_ok=True)
    output_csv = OUT / "berlin_district_sector_proxy_2023.csv"
    seed_columns = [f"seed_{code}" for code in SECTOR_CODES]
    raked_columns = [f"raked_{code}" for code in SECTOR_CODES]
    fields = ["id_bezirk", "bezirk", "j2023g_gwh", "district_weight", *SOURCE_COLUMNS, "detail_total_gwh", "seed_total_gwh", "target_total_gwh", *seed_columns, *raked_columns, "raked_total_gwh", *(f"share_{code}" for code in SECTOR_CODES), "mapping_policy", "public_flag", "transport_flag", "monthly_data_flag", "imputation_flag"]
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in detail:
            writer.writerow({field: f"{row[field]:.9f}" if isinstance(row[field], float) else row[field] for field in fields})

    column_residual = {code: sum(row[f"raked_{code}"] for row in detail) - targets[code] for code in SECTOR_CODES}
    row_residual = [row["raked_total_gwh"] - row["target_total_gwh"] for row in detail]
    share_sums = [sum(row[f"share_{code}"] for code in SECTOR_CODES) for row in detail]
    audit = {
        "status": "proxy_matrix_audited_conditionally",
        "district_count": len(detail),
        "district_reference_total_gwh": spatial_total,
        "umweltatlas_detail_total_gwh": detail_total,
        "detail_vs_district_reference_pct": (detail_total / spatial_total - 1.0) * 100.0,
        "strombilanz_total_gwh": target_total,
        "targets_gwh": targets,
        "seed_totals_gwh": {code: sum(row[f"seed_{code}"] for row in detail) for code in SECTOR_CODES},
        "max_abs_row_residual_gwh": max(abs(value) for value in row_residual),
        "max_abs_column_residual_gwh": max(abs(value) for value in column_residual.values()),
        "column_residual_gwh": column_residual,
        "shares_sum_min": min(share_sums),
        "shares_sum_max": max(share_sums),
        "public_structural_zero": True,
        "monthly_data_available": False,
    }
    audit_json = OUT / "berlin_district_sector_proxy_2023_audit.json"
    audit_json.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit_md = OUT / "berlin_district_sector_proxy_2023_audit.md"
    audit_md.write_text(
        "# Auditoría de matriz proxy distrito–sector de Berlín 2023\n\n"
        "Estado: **matriz construida y reconciliada; validación sectorial independiente pendiente**.\n\n"
        "## Regla aplicada\n\n"
        "Los pesos espaciales provienen de `j2023g` del Umweltatlas. `Haushalt`, `Nachtspeicher` y `Wärmepumpe` se usan como proxy residencial; `Gewerbe` como proxy comercial; `Lastgangkunde` se reparte entre industria, comercio y transporte con la proporción agregada de Strombilanz. La matriz se reconcilia por IPF a los totales sectoriales de Strombilanz y a los totales distritales normalizados al mismo total.\n\n"
        f"- Distritos: **{len(detail)}**.\n- Total distrital `j2023g`: **{spatial_total:.6f} GWh**.\n- Total de detalle Umweltatlas: **{detail_total:.6f} GWh**.\n- Diferencia detalle frente a `j2023g`: **{audit['detail_vs_district_reference_pct']:.6f} %**.\n- Total objetivo Strombilanz: **{target_total:.6f} GWh**.\n- Residuo máximo por distrito después de IPF: **{audit['max_abs_row_residual_gwh']:.12g} GWh**.\n- Residuo máximo por sector después de IPF: **{audit['max_abs_column_residual_gwh']:.12g} GWh**.\n- Suma de shares por distrito: **{audit['shares_sum_min']:.12f}–{audit['shares_sum_max']:.12f}**.\n\n"
        "## Limitaciones\n\n"
        "`Lastgangkunde` no identifica por sí solo industria, comercio ni transporte; su partición es un prior. La categoría pública no es separable en la Strombilanz utilizada y queda con objetivo cero. La matriz es anual: para generar shares mensuales se requiere un perfil temporal sectorial normalizado. Esta salida sirve como insumo de desagregación y no como KPI espacial o sectorial independiente.\n",
        encoding="utf-8",
    )
    manifest = {
        "status": audit["status"],
        "inputs": {str(path.relative_to(REPO)): sha256(path) for path in (DETAIL, DISTRICTS, SECTORS, BALANCE)},
        "outputs": {str(path.relative_to(REPO)): sha256(path) for path in (output_csv, audit_json, audit_md)},
        "mapping_policy": detail[0]["mapping_policy"],
        "monthly_status": "not_available_from_current_inputs",
    }
    (OUT / "berlin_district_sector_proxy_2023_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
