"""Extract annual Berlin sector shares for the multiyear contract.

The corrected Strombilanz workbook contains the historical S.28 table through
2023. Years 2020-2023 are extracted from the first consumption block. The
2024 row is deliberately marked as a frozen 2023 carry-forward for holdout
inference; it is not presented as an observed 2024 Strombilanz value.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

REPO = Path(__file__).resolve().parents[1]
NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
DEFAULT_XLSX = REPO / "prototipo_3/data/de_alemania/external_validation/berlin_2023/SB_E04-04-00_2023j01_BE.xlsx"
DEFAULT_OUTPUT = REPO / "corfo-report/validation/berlin/berlin_sector_shares_multiyear_2020_2024.csv"
DEFAULT_REPORT = REPO / "corfo-report/validation/berlin/berlin_sector_shares_multiyear_2020_2024.md"
SOURCE_YEARS = (2020, 2021, 2022, 2023)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def xlsx_value(cell: ET.Element, shared_strings: list[str]) -> str:
    value = cell.find(f"{{{NS_MAIN}}}v")
    if value is None or value.text is None:
        return ""
    result = value.text
    if cell.attrib.get("t") == "s":
        result = shared_strings[int(result)]
    return result


def xlsx_rows(path: Path, sheet_pattern: str) -> tuple[str, list[dict[str, str]]]:
    with zipfile.ZipFile(path) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall(f"{{{NS_MAIN}}}si"):
                shared_strings.append("".join(node.text or "" for node in item.iter(f"{{{NS_MAIN}}}t")))
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        relmap = {
            node.attrib["Id"]: node.attrib["Target"]
            for node in relationships.findall(f"{{{NS_PKG_REL}}}Relationship")
        }
        for sheet in workbook.find(f"{{{NS_MAIN}}}sheets"):
            name = sheet.attrib["name"]
            if not re.search(sheet_pattern, name, re.IGNORECASE):
                continue
            target = relmap[sheet.attrib[f"{{{NS_REL}}}id"]]
            if not target.startswith("xl/"):
                target = "xl/" + target
            root = ET.fromstring(archive.read(target))
            rows: list[dict[str, str]] = []
            for row in root.findall(f".//{{{NS_MAIN}}}sheetData/{{{NS_MAIN}}}row"):
                values: dict[str, str] = {}
                for cell in row.findall(f"{{{NS_MAIN}}}c"):
                    match = re.match(r"[A-Z]+", cell.attrib.get("r", ""))
                    if match:
                        values[match.group(0)] = xlsx_value(cell, shared_strings)
                rows.append(values)
            return name, rows
    raise ValueError(f"Sheet not found: {sheet_pattern}")


def extract_consumption(path: Path) -> tuple[str, dict[int, dict[str, float]]]:
    sheet, rows = xlsx_rows(path, r"^S\.28_Strombilanz$")
    result: dict[int, dict[str, float]] = {}
    for row in rows:
        try:
            year = int(float(row.get("A", "").strip()))
            total = float(row.get("B", ""))
            industry = float(row.get("C", ""))
            households = float(row.get("D", ""))
            ghd = float(row.get("E", ""))
            transport = float(row.get("F", ""))
        except (TypeError, ValueError):
            continue
        if year not in SOURCE_YEARS or year in result or total <= 1000:
            continue
        result[year] = {
            "total_gwh": total,
            "industry_gwh": industry,
            "households_gwh": households,
            "ghd_gwh": ghd,
            "transport_gwh": transport,
        }
    missing = set(SOURCE_YEARS).difference(result)
    if missing:
        raise ValueError(f"Missing Strombilanz years: {sorted(missing)}")
    return sheet, result


def share_row(year: int, values: dict[str, float], source_year: int, source: str, status: str) -> dict[str, object]:
    total = values["total_gwh"]
    shares = {
        "share_I": values["industry_gwh"] / total,
        "share_R": values["households_gwh"] / total,
        "share_C": values["ghd_gwh"] / total,
        "share_P": 0.0,
        "share_T": values["transport_gwh"] / total,
    }
    if abs(sum(shares.values()) - 1.0) > 1e-9:
        raise ValueError(f"Sector shares do not sum to one for {year}: {shares}")
    return {
        "territory": "Berlin-administrative",
        "year": year,
        "source_year": source_year,
        "region_comuna_share": 1.0,
        "total_gwh": f"{total:.9f}",
        **{key: f"{value:.12f}" for key, value in shares.items()},
        "source": source,
        "share_status": status,
        "sector_mapping_policy": "industria_mineria->I; hogares->R; GHD_otros->C; transporte->T; publico_no_separable->P=0",
        "temporal_resolution": "annual_broadcast",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    xlsx = args.xlsx.resolve()
    output = args.output.resolve()
    report = args.report.resolve()
    sheet, extracted = extract_consumption(xlsx)
    rows = [
        share_row(year, extracted[year], year, "Strombilanz Berlin historical S.28 consumption final", "observed_annual")
        for year in SOURCE_YEARS
    ]
    rows.append(
        share_row(
            2024,
            extracted[2023],
            2023,
            "Strombilanz Berlin 2023 last-available shares",
            "frozen_last_available_for_holdout_only",
        )
    )
    fields = list(rows[0])
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Shares sectoriales anuales multianuales de Berlín",
        "",
        f"Fuente: Strombilanz corregida, hoja {sheet}, XLSX {xlsx.relative_to(REPO)}.",
        f"SHA-256 de la fuente: {sha256(xlsx)}.",
        "",
        "Los años 2020-2023 se extraen del bloque de consumo final de la tabla S.28. El sector público permanece en cero porque la fuente no lo separa. La fila 2024 conserva los shares 2023 únicamente para permitir un holdout con variables congeladas; no es un dato observado de Strombilanz 2024.",
        "",
        "| Año | Año fuente | Total GWh | Industria | Residencial | GHD | Transporte | Público | Estado |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['year']} | {row['source_year']} | {row['total_gwh']} | {row['share_I']} | {row['share_R']} | {row['share_C']} | {row['share_T']} | {row['share_P']} | {row['share_status']} |"
        )
    lines.extend([
        "",
        f"Salida: {output.relative_to(REPO)}.",
        "La tabla está lista para alimentar el contrato multianual, sujeto a la auditoría temporal HV y a la decisión de no usar la fila 2024 como evidencia sectorial independiente.",
    ])
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "report": str(report), "rows": len(rows), "source_sha256": sha256(xlsx)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
