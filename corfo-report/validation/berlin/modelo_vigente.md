# Modelo vigente de reportabilidad — Berlín, Alemania

**Versión vigente:** expansión multianual 2020–2024, dimensión térmica `d=8`.

Esta es la versión que debe utilizarse para reportar los resultados actuales del modelo alemán. La línea base d=3 entrenada únicamente con 2023 se conserva como referencia histórica y de trazabilidad; no representa la versión vigente.

## Contrato vigente

- Entrenamiento: 2020–2022.
- Validación y selección de dimensión: 2023.
- Holdout temporal: 2024.
- Variables objetivo: demanda HV de Stromnetz Berlin, con temperatura DWD y variables calendario/sectoriales.
- Partición: cronológica por año; el shuffle se limita a los lotes de entrenamiento.
- Shares sectoriales: anuales; 2024 usa carry-forward 2023 etiquetado para el holdout.
- Salida espacial: pesos distritales del proxy Umweltatlas 2023, reutilizados en 2020–2024 por falta de una serie distrital anual compatible.

## KPI reportables

| Evaluación | MAPE | Cobertura | Estado |
|---|---:|---:|---|
| Validación 2023, d=8 | 3,452548 % | 8.747/8.760 horas | Cumple MAPE ≤35 % |
| Holdout temporal 2024, d=8 | 3,426289 % | 8.773/8.784 horas | Cumple MAPE ≤35 %; mismo operador |

El holdout 2024 acredita generalización temporal dentro de Stromnetz Berlin. No constituye validación horaria independiente. La desagregación por distrito y sector es una asignación condicionada y no un KPI espacial independiente.

## Evidencia

- [Consolidado multianual](multiyear_2020_2024/berlin_multiyear_consolidated.md)
- [Matriz KPI](../../results/tables/berlin_multiyear_kpi_compliance.csv)
- [Figuras y manifiesto](../../results/figures/berlin_multiyear_reportability_manifest.json)
- [Auditoría espacial](multiyear_2020_2024/berlin_multiyear_spatial_postprocess_audit.md)

