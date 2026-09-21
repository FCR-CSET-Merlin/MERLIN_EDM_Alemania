# Reportabilidad CORFO — Alemania

Esta es la carpeta activa de reportabilidad del fork alemán de MERLIN EDM. Contendrá exclusivamente evidencia generada para Alemania, comenzando por el piloto de reconstrucción histórica de Berlín.

Los resultados heredados de Chile se conservan en [`corfo-report-chile-referencia/`](../corfo-report-chile-referencia/). No deben citarse como evidencia de un KPI alemán.

La estructura sigue el [estándar de reportabilidad CORFO](https://github.com/FCR-CSET-Merlin/merlin-index/blob/main/08-reportaje-corfo/estandar-estructura-corfo-report.md), separando resultados, validación, reproducibilidad y evidencia KPI.

## Estado actual

| Elemento | Estado |
|---|---|
| Caso piloto | Berlín, Alemania |
| Objetivo | Reconstrucción histórica de demanda eléctrica horaria |
| Fuentes alemanas | Candidatas; BKG `11000` aceptado para el perímetro piloto; cobertura, unidades, licencia y semántica HV siguen en revisión |
| Modelo alemán | No ejecutado en esta etapa |
| KPI alemán | No evaluado; no se declara cumplimiento |
| Próximo producto | Auditoría HV 2019–2023, balance anual y dictamen de factibilidad |

## Resultados previstos

| Resultado | Ubicación | Regla |
|---|---|---|
| Tablas reconstruidas | [`results/tables/`](results/tables/) | Solo Alemania, con año, territorio, sector y unidad |
| Figuras | [`results/figures/`](results/figures/) | Fuente, cobertura y fecha de generación |
| Series horarias | [`results/timeseries/`](results/timeseries/) | Pesadas fuera de Git; índice y hash obligatorios |
| Auditoría de fuentes | [`validation/sources/`](validation/sources/) | Cobertura, perímetro, licencia y transformaciones |
| Validación Berlín | [`validation/berlin/`](validation/berlin/) | Comparaciones por año, territorio y sector |
| KPI | [`validation/kpi_plan.md`](validation/kpi_plan.md) | Fórmula, umbral, denominador e independencia |
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

La matriz y el dictamen se documentan en [`PLAN_TRABAJO_ADAPTACION_ALEMANIA.md`](../PLAN_TRABAJO_ADAPTACION_ALEMANIA.md).

## KPI y reproducibilidad

La meta operativa es MAPE ≤35 %. Cada resultado debe indicar si mide demanda de red, consumo final o consistencia condicionada. No se publica `cumple` sin una fila en `kpi_validation.csv`, una explicación en `cumplimiento_kpi.md` y un manifiesto reproducible.

Cada corrida registra commit, entorno, modelo, scaler, columnas, URL/fecha/licencia/hash de fuentes, período, zona horaria, cobertura, faltantes, transformaciones, perímetro y hashes de salida.

Todavía no existen resultados alemanes ni una evaluación KPI; esta carpeta contiene el plan y las plantillas de evidencia.
