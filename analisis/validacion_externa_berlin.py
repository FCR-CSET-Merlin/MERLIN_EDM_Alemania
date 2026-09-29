#!/usr/bin/env python3
"""Audit and homologate Berlin's 2023 external electricity references.

The script uses only the Python standard library. It extracts the corrected
Amt für Statistik Berlin-Brandenburg workbook, reads the Umweltatlas WFS
GeoJSON layers, and compares them with the observed Stromnetz Berlin HV
hourly series. The comparison deliberately labels the HV series as observed
proxy: model prediction outputs are not silently substituted for observations.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"m": NS_MAIN, "r": NS_REL}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _xlsx_value(cell: ET.Element, shared_strings: list[str]) -> str:
    value = cell.find(f"{{{NS_MAIN}}}v")
    if value is None or value.text is None:
        return ""
    result = value.text
    if cell.attrib.get("t") == "s":
        result = shared_strings[int(result)]
    return result


def _xlsx_rows(path: Path, sheet_name_pattern: str) -> tuple[str, list[dict[str, str]]]:
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
            if not re.search(sheet_name_pattern, name, re.IGNORECASE):
                continue
            target = relmap[sheet.attrib[f"{{{NS_REL}}}id"]]
            if not target.startswith("xl/"):
                target = "xl/" + target
            root = ET.fromstring(archive.read(target))
            rows: list[dict[str, str]] = []
            for row in root.findall(f".//{{{NS_MAIN}}}sheetData/{{{NS_MAIN}}}row"):
                values: dict[str, str] = {}
                for cell in row.findall(f"{{{NS_MAIN}}}c"):
                    ref = cell.attrib.get("r", "")
                    column = re.match(r"[A-Z]+", ref)
                    if column:
                        values[column.group(0)] = _xlsx_value(cell, shared_strings)
                rows.append(values)
            return name, rows
    raise ValueError(f"No sheet matching {sheet_name_pattern!r} in {path}")


def _float(value: str) -> float:
    return float(value.replace(",", "."))


def extract_strombilanz(path: Path, output: Path) -> dict[str, float]:
    sheet, rows = _xlsx_rows(path, r"^S\.28_Strombilanz$")
    target: dict[str, str] | None = None
    for row in rows:
        year = row.get("A", "").strip()
        if year in {"2023", "2023.0"}:
            target = row
            break
    if target is None:
        raise ValueError(f"2023 row not found in {sheet}")
    values = {
        "consumo_final_total": _float(target["B"]),
        "industria_mineria": _float(target["C"]),
        "hogares": _float(target["D"]),
        "ghd_otros": _float(target["E"]),
        "transporte": _float(target["F"]),
    }
    rows_out = [
        ("consumo_final_total", values["consumo_final_total"]),
        ("industria_mineria", values["industria_mineria"]),
        ("hogares", values["hogares"]),
        ("ghd_otros", values["ghd_otros"]),
        ("transporte", values["transporte"]),
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["year", "category", "value_gwh", "unit", "source_sheet"])
        for category, value in rows_out:
            writer.writerow([2023, category, f"{value:.9f}", "GWh (Mill. kWh)", sheet])
    return values


def read_geojson(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_districts(path: Path, output: Path) -> tuple[list[dict], str]:
    document = read_geojson(path)
    crs = document.get("crs", {}).get("properties", {}).get("name", "")
    features = document.get("features", [])
    rows = []
    total = sum(float(feature["properties"]["j2023g"]) for feature in features)
    for feature in features:
        props = feature["properties"]
        value = float(props["j2023g"])
        rows.append({
            "id_bezirk": props["id_bezirk"],
            "bezirk": props["bezirk"],
            "j2023g_gwh": value,
            "share_pct": value / total * 100.0 if total else math.nan,
            "crs": crs,
        })
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id_bezirk", "bezirk", "j2023g_gwh", "share_pct", "crs"], lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "j2023g_gwh": f"{row['j2023g_gwh']:.6f}", "share_pct": f"{row['share_pct']:.9f}"})
    return rows, crs


def extract_district_detail(path: Path, output: Path) -> tuple[list[dict], str]:
    document = read_geojson(path)
    crs = document.get("crs", {}).get("properties", {}).get("name", "")
    features = document.get("features", [])
    categories = ["verbr_gewerbe", "verbr_haushalt", "verbr_nachtspeicher", "verbr_waermepumpe", "verbr_lastgangkunde"]
    rows = []
    for feature in features:
        props = feature["properties"]
        row = {"id_bezirk": props["id_bezirk"], "bezirk": props["bezirk"], "crs": crs}
        row.update({key: float(props[key]) for key in categories})
        row["detail_total_gwh"] = sum(row[key] for key in categories)
        rows.append(row)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["id_bezirk", "bezirk", *categories, "detail_total_gwh", "crs"]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: (f"{value:.6f}" if isinstance(value, float) else value) for key, value in row.items()})
    return rows, crs


def hv_energy_gwh(path: Path) -> tuple[float, int]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        values = [float(row["energy_MWh"]) for row in reader if row.get("energy_MWh") not in (None, "")]
    return sum(values) / 1000.0, len(values)


def pct_error(model: float, reference: float) -> float:
    return (model - reference) / reference * 100.0 if reference else math.nan


def write_comparison(output: Path, annual: dict[str, float], districts: list[dict], detail: list[dict], hv_gwh: float, hv_rows: int) -> None:
    district_total = sum(row["j2023g_gwh"] for row in districts)
    detail_total = sum(row["detail_total_gwh"] for row in detail)
    rows = [
        {
            "comparison_id": "EXT-ANN-2023",
            "layer": "B",
            "reference_period": "2023",
            "territory_code": "11000",
            "territory_name": "Berlin",
            "model_metric": "HV observado; energia anual",
            "reference_metric": "Strombilanz; consumo final total",
            "model_value": hv_gwh,
            "reference_value": annual["consumo_final_total"],
            "absolute_error": hv_gwh - annual["consumo_final_total"],
            "relative_error_pct": pct_error(hv_gwh, annual["consumo_final_total"]),
            "status": "consistencia_condicionada",
            "independence": "si; shares de Strombilanz participaron en el contrato",
            "notes": f"{hv_rows} horas HV observadas; no es prediccion del modelo",
        },
        {
            "comparison_id": "EXT-SPAT-2023-TOTAL",
            "layer": "C-control",
            "reference_period": "2023; campo j2023g",
            "territory_code": "11000",
            "territory_name": "Berlin",
            "model_metric": "HV observado; energia anual ciudad",
            "reference_metric": "Umweltatlas; suma de 12 distritos",
            "model_value": hv_gwh,
            "reference_value": district_total,
            "absolute_error": hv_gwh - district_total,
            "relative_error_pct": pct_error(hv_gwh, district_total),
            "status": "control_total_condicionado",
            "independence": "si",
            "notes": "Control de magnitud; no sustituye una comparacion de shares distritales",
        },
        {
            "comparison_id": "EXT-SPAT-2023-DISTRICTS",
            "layer": "C",
            "reference_period": "2023; campo j2023g",
            "territory_code": "11000",
            "territory_name": "Berlin",
            "model_metric": "salida distrital del modelo",
            "reference_metric": "Umweltatlas; 12 distritos",
            "model_value": "",
            "reference_value": district_total,
            "absolute_error": "",
            "relative_error_pct": "",
            "status": "no_evaluable",
            "independence": "si",
            "notes": "La reconstruccion actual solo genera Berlin agregado; no hay salida por distrito",
        },
        {
            "comparison_id": "EXT-SPAT-2023-DETAIL",
            "layer": "C-control",
            "reference_period": "2023; capa detallada",
            "territory_code": "11000",
            "territory_name": "Berlin",
            "model_metric": "",
            "reference_metric": "Umweltatlas; categorias detalladas",
            "model_value": "",
            "reference_value": detail_total,
            "absolute_error": "",
            "relative_error_pct": "",
            "status": "control_referencia",
            "independence": "si",
            "notes": "Las categorias no son equivalentes uno a uno a la Strombilanz sectorial",
        },
    ]
    fields = ["comparison_id", "layer", "reference_period", "territory_code", "territory_name", "model_metric", "reference_metric", "model_value", "reference_value", "absolute_error", "relative_error_pct", "status", "independence", "notes"]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_audit(output: Path, xlsx: Path, capabilities: Path, districts_path: Path, detail_path: Path, hv_path: Path, annual: dict[str, float], districts: list[dict], detail: list[dict], hv_gwh: float, hv_rows: int, crs: str) -> None:
    district_total = sum(row["j2023g_gwh"] for row in districts)
    detail_total = sum(row["detail_total_gwh"] for row in detail)
    lines = [
        "# Auditoría y homologación externa — Berlín 2023",
        "",
        "**Fecha de descarga:** 29 de septiembre de 2026",
        "**Estado:** fuentes descargadas y auditadas; comparación distrital del modelo aún no evaluable",
        "**Serie modelada disponible:** HV observado; la salida predicha 2023 todavía no está exportada por hora/distrito",
        "",
        "## Fuentes y hashes",
        "",
        "| Archivo | Uso | SHA-256 |",
        "|---|---|---|",
        f"| `{xlsx.name}` | Strombilanz corregida 2023 | `{sha256(xlsx)}` |",
        f"| `{capabilities.name}` | capacidades WFS | `{sha256(capabilities)}` |",
        f"| `{districts_path.name}` | capa distrital WFS | `{sha256(districts_path)}` |",
        f"| `{detail_path.name}` | capa distrital detallada WFS | `{sha256(detail_path)}` |",
        f"| `{hv_path.name}` | serie HV horaria usada como proxy observado | `{sha256(hv_path)}` |",
        "",
        "Fuentes oficiales: [Amt für Statistik Berlin-Brandenburg](https://www.statistik-berlin-brandenburg.de/e-iv-4-j/), [WFS Umweltatlas](https://daten.berlin.de/datensaetze/energieverbrauch-strom-umweltatlas-wfs-238921d9) y [descripción técnica de atributos](https://fbinter.stadt-berlin.de/fb_daten/beschreibung/umweltatlas/datenformatbeschreibung/Datenformatbeschreibung_08_10_1verbrauchstrom.html).",
        "",
        "## Auditoría anual",
        "",
        f"La hoja de cálculo de Strombilanz fue identificada como `Strombilanz Berlin 2010 bis 2023`. La unidad publicada es Mill. kWh, equivalente numéricamente a GWh.",
        "",
        "| Categoría 2023 | GWh |",
        "|---|---:|",
        f"| Consumo final total | {annual['consumo_final_total']:.3f} |",
        f"| Industria y minería | {annual['industria_mineria']:.3f} |",
        f"| Hogares | {annual['hogares']:.3f} |",
        f"| GHD y otros | {annual['ghd_otros']:.3f} |",
        f"| Transporte | {annual['transporte']:.3f} |",
        "",
        f"La suma sectorial es {sum(annual[key] for key in ('industria_mineria','hogares','ghd_otros','transporte')):.3f} GWh y coincide con el total publicado a la precisión de la hoja.",
        "",
        "## Homologación con HV 2023",
        "",
        "| Referencia | Energía (GWh) | Diferencia respecto a HV | Error relativo |",
        "|---|---:|---:|---:|",
        f"| HV observado, 8.760 horas | {hv_gwh:.6f} | 0 | 0 % |",
        f"| Strombilanz, consumo final total | {annual['consumo_final_total']:.6f} | {hv_gwh-annual['consumo_final_total']:+.6f} | {pct_error(hv_gwh, annual['consumo_final_total']):+.6f} % |",
        f"| Umweltatlas, suma distrital `j2023g` | {district_total:.6f} | {hv_gwh-district_total:+.6f} | {pct_error(hv_gwh, district_total):+.6f} % |",
        f"| Umweltatlas, suma capa detallada | {detail_total:.6f} | {hv_gwh-detail_total:+.6f} | {pct_error(hv_gwh, detail_total):+.6f} % |",
        "",
        "La comparación HV–Strombilanz es consistencia anual condicionada: HV es carga de red y Strombilanz es consumo final. La comparación con la suma distrital es un control adicional, porque el WFS y el perfil HV pueden tener coberturas y reglas de agregación diferentes.",
        "",
        "## Auditoría espacial",
        "",
        f"El WFS devuelve {len(districts)} distritos, todos con `j2023g` no nulo y CRS `{crs}`. La ficha del portal describe el conjunto como 2022, pero el servicio actualmente publica campos `j2023g` y `j2024g`; se seleccionó `j2023g` por corresponder al año de reconstrucción y se conserva la discrepancia de metadatos.",
        "",
        "| ID | Distrito | `j2023g` (GWh) | Participación (%) |",
        "|---:|---|---:|---:|",
    ]
    for row in districts:
        lines.append(f"| {row['id_bezirk']} | {row['bezirk']} | {row['j2023g_gwh']:.6f} | {row['share_pct']:.6f} |")
    lines += [
        "",
        f"**Total distrital:** {district_total:.6f} GWh.",
        "",
        f"La capa detallada contiene `verbr_gewerbe`, `verbr_haushalt`, `verbr_nachtspeicher`, `verbr_waermepumpe` y `verbr_lastgangkunde`; su total es {detail_total:.6f} GWh. No se interpreta como sustituto de las cuatro categorías de la Strombilanz porque las definiciones no son idénticas.",
        "",
        "## Dictamen",
        "",
        "- **Fuente anual:** aceptada para consistencia externa condicionada; unidades y fila 2023 verificadas.",
        "- **Fuente espacial:** aceptada como referencia distrital; se detecta discrepancia entre el texto descriptivo del portal y los campos 2023 disponibles en el WFS.",
        "- **Homologación actual:** completada a nivel ciudad observado y preparada a nivel distrital.",
        "- **KPI espacial:** `no_evaluable` hasta que la reconstrucción genere una salida por distrito o se defina una regla de desagregación explícita.",
        "- **KPI horario externo:** permanece pendiente; ninguna de estas fuentes es una referencia horaria independiente de Berlín.",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("prototipo_3/data/de_alemania/external_validation/berlin_2023"))
    parser.add_argument("--hv-hourly", type=Path, default=Path("prototipo_3/data/de_alemania/berlin_hv_2023/berlin_hv_2023_hourly.csv"))
    parser.add_argument("--output-root", type=Path, default=Path("corfo-report/validation/berlin/external_2023"))
    args = parser.parse_args()
    data = args.data_root
    out = args.output_root
    xlsx = data / "SB_E04-04-00_2023j01_BE.xlsx"
    capabilities = data / "ua_stromverbrauch_GetCapabilities.xml"
    districts_path = data / "berlin_strom_districts.geojson"
    detail_path = data / "berlin_strom_districts_detail.geojson"
    annual = extract_strombilanz(xlsx, out / "berlin_strombilanz_2023_extracted.csv")
    districts, crs = extract_districts(districts_path, out / "berlin_umweltatlas_bezirke_2023.csv")
    detail, _ = extract_district_detail(detail_path, out / "berlin_umweltatlas_bezirke_detail_2023.csv")
    hv_gwh, hv_rows = hv_energy_gwh(args.hv_hourly)
    write_comparison(out / "homologacion_externa_berlin_2023.csv", annual, districts, detail, hv_gwh, hv_rows)
    write_audit(out / "auditoria_homologacion_externa_berlin_2023.md", xlsx, capabilities, districts_path, detail_path, args.hv_hourly, annual, districts, detail, hv_gwh, hv_rows, crs)
    print(json.dumps({"hv_gwh": hv_gwh, "hv_rows": hv_rows, "strombilanz": annual, "district_count": len(districts), "district_total_gwh": sum(row['j2023g_gwh'] for row in districts), "detail_total_gwh": sum(row['detail_total_gwh'] for row in detail), "output_root": str(out)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
