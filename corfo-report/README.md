# Reportabilidad CORFO — Alemania

Esta es la carpeta activa de reportabilidad del fork alemán de MERLIN EDM. Contendrá exclusivamente evidencia generada para Alemania, comenzando por el piloto de reconstrucción histórica de Berlín.

Los resultados heredados de Chile se conservan en [`corfo-report-chile-referencia/`](../corfo-report-chile-referencia/). No deben citarse como evidencia de un KPI alemán.

La estructura sigue el [estándar de reportabilidad CORFO](https://github.com/FCR-CSET-Merlin/merlin-index/blob/main/08-reportaje-corfo/estandar-estructura-corfo-report.md), separando resultados, validación, reproducibilidad y evidencia KPI.

## Estado actual

> **Versión reportable vigente:** expansión multianual 2020–2024, dimensión `d=8`. La línea base 2023 `d=3` se conserva exclusivamente como referencia histórica.

| Elemento | Estado |
|---|---|
| Caso piloto | Berlín, Alemania |
| Objetivo | Reconstrucción histórica de demanda eléctrica horaria |
| Fuentes alemanas | Strombilanz histórica 2020–2023, Umweltatlas WFS y DWD auditados; BKG `11000` aceptado; alcance exacto HV y timestamps del operador siguen pendientes |
| Modelo alemán vigente | Expansión multianual `d=8`; entrenamiento 2020–2022, validación 2023 y holdout temporal 2024; 43.677 horas completas |
| KPI alemán vigente | Validación 2023 = 3,452548 %; holdout temporal 2024 = 3,426289 %; ambos ≤35 % |
| Próximo producto | Mantener la expansión multianual como versión reportable y cerrar las limitaciones territoriales/sectoriales |

## Resultados previstos

| Resultado | Ubicación | Regla |
|---|---|---|
| Tablas reconstruidas | [`results/tables/`](results/tables/) | Solo Alemania, con año, territorio, sector y unidad |
| Figuras | [`results/figures/`](results/figures/) | Fuente, cobertura y fecha de generación |

La [salida d=3 de 2023](results/figures/berlin_demanda_distrital_d3_2023.png) y sus tablas se conservan como referencia histórica; no son la versión vigente del modelo.

Para la expansión multianual 2020–2024 se generaron la [figura comparativa de MAPE (PNG)](results/figures/berlin_multiyear_kpi_mape.png), su [versión vectorial (SVG)](results/figures/berlin_multiyear_kpi_mape.svg), la [figura de cobertura d=8 (PNG)](results/figures/berlin_multiyear_d8_coverage.png), su [versión vectorial (SVG)](results/figures/berlin_multiyear_d8_coverage.svg) y el [manifiesto con hashes](results/figures/berlin_multiyear_reportability_manifest.json).

La salida espacial multianual está disponible como [mapa anual por distrito](results/figures/berlin_demanda_distrital_multiyear_d8_2020_2024.png), [mapa anual distrito–sector](results/figures/berlin_demanda_distrito_sector_anual_multiyear_d8_2020_2024.png), [tabla distrital](results/tables/berlin_multiyear_d8_district_annual.csv), [tabla distrito–sector](results/tables/berlin_multiyear_d8_district_sector_annual.csv) y [auditoría de conservación y limitaciones](validation/berlin/multiyear_2020_2024/berlin_multiyear_spatial_postprocess_audit.md). Ambas figuras incorporan una barra de color común con las magnitudes del heatmap.
| Series horarias | [`results/timeseries/`](results/timeseries/) | Pesadas fuera de Git; índice y hash obligatorios |
| Auditoría de fuentes | [`validation/sources/`](validation/sources/) | Cobertura, perímetro, licencia y transformaciones |
| Validación Berlín | [`validation/berlin/`](validation/berlin/) | Comparaciones por año, territorio y sector |
| KPI | [`validation/kpi_plan.md`](validation/kpi_plan.md), [`validation/berlin/kpi_validation.csv`](validation/berlin/kpi_validation.csv), [`results/tables/kpi_summary.csv`](results/tables/kpi_summary.csv) | Fórmula, umbral, denominador e independencia |
| KPI expansión multianual | [`results/tables/berlin_multiyear_kpi_compliance.csv`](results/tables/berlin_multiyear_kpi_compliance.csv), [`results/tables/berlin_multiyear_kpi_compliance.md`](results/tables/berlin_multiyear_kpi_compliance.md), [ledger canónico](validation/berlin/kpi_validation.csv) | MAPE ≤35 %, partición, comparador, independencia, estado y evidencia |
| Contrato de validación | [`validation/sources/contrato_validacion_berlin.md`](validation/sources/contrato_validacion_berlin.md) | Capas interna, anual, espacial y horaria |
| Matriz comparadores | [`validation/sources/comparaciones_externas_berlin.csv`](validation/sources/comparaciones_externas_berlin.csv) | Fuentes, perímetro, dependencia y estado |
| Plantilla resultados externos | [`validation/berlin/comparaciones_externas_2023.csv`](validation/berlin/comparaciones_externas_2023.csv) | Métricas sin resultados inventados |
| Ficha | [`validation/ficha_evidencia_berlin.md`](validation/ficha_evidencia_berlin.md) | `cumple`, `no cumple` o `no evaluable` |
| Manifiesto | [`validation/manifiesto_berlin.json`](validation/manifiesto_berlin.json) | Commits, entradas, salidas y hashes |
| Registro de avance | [`validation/registro_avance.md`](validation/registro_avance.md) | Estado por fase, decisiones y siguiente acción |

## Fuentes candidatas

- [Stromnetz Berlin](https://www.stromnetz.berlin/uber-uns/veroffentlichungspflichten/energiewirtschaftsgesetz-enwg/)
- [Statistik Berlin-Brandenburg](https://www.statistik-berlin-brandenburg.de/e-iv-4-j/)
- [Umweltatlas Berlin](https://daten.berlin.de/datensaetze/energieverbrauch-strom-umweltatlas-wfs-238921d9)
- [SMARD](https://www.smard.de/page/en/wiki-article/6078/6036/electricity-consumption)
- [DWD](https://www.dwd.de/EN/ourservices/cdc/cdc.html?lsbId=646268) y [ERA5-Land](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=documentation)
- [Destatis/GENESIS](https://www.destatis.de/EN/Service/OpenData/api-webservice.html), [Zensus 2022](https://www.destatis.de/zensus2022?nn=1344278) y [BKG VG250](https://gdz.bkg.bund.de/index.php/default/wfs-verwaltungsgebiete-1-250-000-stand-01-01-wfs-vg250.html)
- [Decisión territorial del piloto](validation/sources/decision_perimetro_berlin.md)
- [Auditoría de Strombilanz 2023](validation/sources/statistik_berlin_strombilanz_2023_auditoria.md)
- [Contrato de validación de Berlín](validation/sources/contrato_validacion_berlin.md)
- [Investigación de fuentes para validación externa](validation/sources/validacion_externa_demanda_electrica_berlin_contexto.md)
- [Matriz de comparaciones externas](validation/sources/comparaciones_externas_berlin.csv)
- [Plantilla/resultados externos 2023](validation/berlin/comparaciones_externas_2023.csv)
- [Auditoría y homologación externa 2023](validation/berlin/external_2023/auditoria_homologacion_externa_berlin_2023.md)
- [Normalización temporal HV 2023](validation/sources/normalizacion_temporal_hv_2023.md)
- [Auditoría DWD Berlin-Tempelhof 2023](validation/sources/dwd_berlin_tempelhof_2023_auditoria.md)
- [Tabla integrada HV–temperatura](validation/sources/berlin_hv_temperature_features_2023.md)
- [Diagnóstico FNN de temperatura](validation/sources/fnn_berlin_temperature_2023.md)
- [Preparación de ablación de rezagos d=3/d=5/d=8](validation/sources/lag_ablation_berlin_2023.md)
- [Contrato de entrenamiento alemán](validation/sources/contrato_entrenamiento_berlin_2023.md)
- [Ablación predictiva de rezagos](validation/sources/lag_ablation_predictiva_berlin_2023.md)

La matriz y el dictamen se documentan en [`PLAN_TRABAJO_ADAPTACION_ALEMANIA.md`](../PLAN_TRABAJO_ADAPTACION_ALEMANIA.md).

## KPI y reproducibilidad

La meta operativa es MAPE ≤35 %. Cada resultado debe indicar si mide demanda de red, consumo final o consistencia condicionada. No se publica `cumple` sin una fila en `kpi_validation.csv`, una explicación en `cumplimiento_kpi.md` y un manifiesto reproducible.

Cada corrida registra commit, entorno, modelo, scaler, columnas, URL/fecha/licencia/hash de fuentes, período, zona horaria, cobertura, faltantes, transformaciones, perímetro y hashes de salida.

La inferencia d=3 y su KPI horario se conservan como referencia histórica; el modelo vigente d=8 se evalúa sobre las particiones multianuales HV y tampoco sustituye un comparador externo independiente.

La expansión multianual conserva su evidencia en una matriz separada y en el ledger canónico mediante el identificador `CORFO-MERLIN-EDM-DE-BERLIN-MULTIYEAR`. El holdout 2024 se reporta como generalización temporal del mismo operador, no como validación horaria independiente.

La ficha que identifica la versión reportable vigente está en [`validation/berlin/modelo_vigente.md`](validation/berlin/modelo_vigente.md).
