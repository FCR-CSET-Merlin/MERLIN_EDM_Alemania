# Matriz de cumplimiento KPI — expansión multianual de Berlín 2020–2024

**Criterio comprometido:** MAPE horario ≤35 %. Las filas se reportan por dimensión y partición; el holdout 2024 es temporal y pertenece al mismo operador Stromnetz Berlin.

| KPI | d | Partición | Periodo | n válidas | MAPE (%) | Umbral (%) | Cumple | Comparador independiente | Estado |
|---|---:|---|---|---:|---:|---:|---|---|---|
| BERLIN-MULTIYEAR-MAPE-D3-TRAIN | 3 | entrenamiento | 2020-2022 | 26172 | 2.676727 | 35.0 | Sí | No | cumple_entrenamiento |
| BERLIN-MULTIYEAR-MAPE-D3-VALIDATION | 3 | validación 2023 | 2023 | 8752 | 3.904288 | 35.0 | Sí | No | cumple_validacion |
| BERLIN-MULTIYEAR-MAPE-D3-TEST | 3 | holdout temporal 2024 | 2024 | 8778 | 3.846283 | 35.0 | Sí | No | cumple_holdout_temporal_mismo_operador |
| BERLIN-MULTIYEAR-MAPE-D5-TRAIN | 5 | entrenamiento | 2020-2022 | 26166 | 4.624036 | 35.0 | Sí | No | cumple_entrenamiento |
| BERLIN-MULTIYEAR-MAPE-D5-VALIDATION | 5 | validación 2023 | 2023 | 8750 | 4.017141 | 35.0 | Sí | No | cumple_validacion |
| BERLIN-MULTIYEAR-MAPE-D5-TEST | 5 | holdout temporal 2024 | 2024 | 8776 | 4.186405 | 35.0 | Sí | No | cumple_holdout_temporal_mismo_operador |
| BERLIN-MULTIYEAR-MAPE-D8-TRAIN | 8 | entrenamiento | 2020-2022 | 26157 | 2.884490 | 35.0 | Sí | No | cumple_entrenamiento |
| BERLIN-MULTIYEAR-MAPE-D8-VALIDATION | 8 | validación 2023 | 2023 | 8747 | 3.452548 | 35.0 | Sí | No | cumple_validacion |
| BERLIN-MULTIYEAR-MAPE-D8-TEST | 8 | holdout temporal 2024 | 2024 | 8773 | 3.426289 | 35.0 | Sí | No | cumple_holdout_temporal_mismo_operador |

**Configuración seleccionada:** d=8 por menor MAPE de validación 2023 (3.452548 %). El holdout 2024 de esta configuración es 3.426289 %.

**Alcance de la evidencia:** todos los MAPE cumplen el umbral operativo. La evidencia demuestra ajuste, selección y generalización temporal dentro de Stromnetz Berlin; no acredita una validación horaria independiente.

**Controles de fuentes:** la tabla `berlin_multiyear_source_coverage.csv` registra horas HV, filas completas d=8, faltantes DWD y etiquetas DST por año. Las filas sin features completas se excluyen sin imputación.

Figuras asociadas: `berlin_multiyear_kpi_mape.svg/.png` y `berlin_multiyear_d8_coverage.svg/.png`.
