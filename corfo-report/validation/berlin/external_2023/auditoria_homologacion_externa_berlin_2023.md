# Auditoría y homologación externa — Berlín 2023

**Fecha de descarga:** 29 de septiembre de 2026
**Estado:** fuentes descargadas y auditadas; comparación distrital del modelo aún no evaluable
**Serie modelada disponible:** HV observado; la salida predicha 2023 todavía no está exportada por hora/distrito

## Fuentes y hashes

| Archivo | Uso | SHA-256 |
|---|---|---|
| `SB_E04-04-00_2023j01_BE.xlsx` | Strombilanz corregida 2023 | `5b9acbf60a48526c5a25c2a92f8343a9387327071e69418918bded08b7031cce` |
| `ua_stromverbrauch_GetCapabilities.xml` | capacidades WFS | `23c7842236be80b28b04ea41a6c94c3f9f6af623878f8108fd324f15dffcbb8a` |
| `berlin_strom_districts.geojson` | capa distrital WFS | `9ae3d44df152a3a58e511c75dde266e692325fd00ec8f4d6f00853aeabc018e2` |
| `berlin_strom_districts_detail.geojson` | capa distrital detallada WFS | `87454f14a5253e78ac4c4067ce4fe1939aeadb84c96ef307f413e38e0a061e06` |
| `berlin_hv_2023_hourly.csv` | serie HV horaria usada como proxy observado | `ecf47a49ebd665af7ab15717584e893453f01921f5c4aebdfc43141113d1567d` |

Fuentes oficiales: [Amt für Statistik Berlin-Brandenburg](https://www.statistik-berlin-brandenburg.de/e-iv-4-j/), [WFS Umweltatlas](https://daten.berlin.de/datensaetze/energieverbrauch-strom-umweltatlas-wfs-238921d9) y [descripción técnica de atributos](https://fbinter.stadt-berlin.de/fb_daten/beschreibung/umweltatlas/datenformatbeschreibung/Datenformatbeschreibung_08_10_1verbrauchstrom.html).

## Auditoría anual

La hoja de cálculo de Strombilanz fue identificada como `Strombilanz Berlin 2010 bis 2023`. La unidad publicada es Mill. kWh, equivalente numéricamente a GWh.

| Categoría 2023 | GWh |
|---|---:|
| Consumo final total | 11780.229 |
| Industria y minería | 1293.994 |
| Hogares | 3965.647 |
| GHD y otros | 5608.947 |
| Transporte | 911.641 |

La suma sectorial es 11780.229 GWh y coincide con el total publicado a la precisión de la hoja.

## Homologación con HV 2023

| Referencia | Energía (GWh) | Diferencia respecto a HV | Error relativo |
|---|---:|---:|---:|
| HV observado, 8.760 horas | 11812.177946 | 0 | 0 % |
| Strombilanz, consumo final total | 11780.229000 | +31.948946 | +0.271208 % |
| Umweltatlas, suma distrital `j2023g` | 11899.370000 | -87.192054 | -0.732745 % |
| Umweltatlas, suma capa detallada | 11758.050000 | +54.127946 | +0.460348 % |

La comparación HV–Strombilanz es consistencia anual condicionada: HV es carga de red y Strombilanz es consumo final. La comparación con la suma distrital es un control adicional, porque el WFS y el perfil HV pueden tener coberturas y reglas de agregación diferentes.

## Auditoría espacial

El WFS devuelve 12 distritos, todos con `j2023g` no nulo y CRS `urn:ogc:def:crs:EPSG::25833`. La ficha del portal describe el conjunto como 2022, pero el servicio actualmente publica campos `j2023g` y `j2024g`; se seleccionó `j2023g` por corresponder al año de reconstrucción y se conserva la discrepancia de metadatos.

| ID | Distrito | `j2023g` (GWh) | Participación (%) |
|---:|---|---:|---:|
| 01 | Mitte | 2303.910000 | 19.361613 |
| 02 | Friedrichshain-Kreuzberg | 1120.200000 | 9.413944 |
| 03 | Pankow | 813.320000 | 6.834984 |
| 04 | Charlottenburg-Wilmersdorf | 1181.510000 | 9.929181 |
| 05 | Spandau | 885.600000 | 7.442411 |
| 06 | Steglitz-Zehlendorf | 827.520000 | 6.954318 |
| 07 | Tempelhof-Schöneberg | 1110.150000 | 9.329486 |
| 08 | Neukölln | 823.490000 | 6.920450 |
| 09 | Treptow-Köpenick | 747.820000 | 6.284534 |
| 10 | Marzahn-Hellersdorf | 569.290000 | 4.784203 |
| 11 | Lichtenberg | 604.470000 | 5.079849 |
| 12 | Reinickendorf | 912.090000 | 7.665028 |

**Total distrital:** 11899.370000 GWh.

La capa detallada contiene `verbr_gewerbe`, `verbr_haushalt`, `verbr_nachtspeicher`, `verbr_waermepumpe` y `verbr_lastgangkunde`; su total es 11758.050000 GWh. No se interpreta como sustituto de las cuatro categorías de la Strombilanz porque las definiciones no son idénticas.

## Dictamen

- **Fuente anual:** aceptada para consistencia externa condicionada; unidades y fila 2023 verificadas.
- **Fuente espacial:** aceptada como referencia distrital; se detecta discrepancia entre el texto descriptivo del portal y los campos 2023 disponibles en el WFS.
- **Homologación actual:** completada a nivel ciudad observado y preparada a nivel distrital.
- **KPI espacial:** `no_evaluable` hasta que la reconstrucción genere una salida por distrito o se defina una regla de desagregación explícita.
- **KPI horario externo:** permanece pendiente; ninguna de estas fuentes es una referencia horaria independiente de Berlín.
