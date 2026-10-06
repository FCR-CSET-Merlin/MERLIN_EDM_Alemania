# Consolidado de la expansión multianual de Berlín 2020-2024

Estado: **PASS**. Se integraron HV/DWD, shares sectoriales, contratos y métricas MLP en una sola evidencia.

## Diseño experimental

- Entrenamiento: años 2020-2022.
- Validación y selección de dimensión: año 2023.
- Holdout temporal congelado: año 2024.
- Shuffle: solo dentro del entrenamiento; no se mezclaron años entre particiones.
- Scaler del objetivo: ajustado únicamente con entrenamiento.

## Cobertura y control de fuentes

| Año | Horas HV | Filas completas d=8 | Cobertura d=8 | Faltantes DWD | Desajustes de etiqueta HV | Energía HV (GWh) |
|---:|---:|---:|---:|---:|---:|---:|
| 2020 | 8784 | 8784 | 100.000000 % | 0 | 20166 | 12247.204540 |
| 2021 | 8760 | 8760 | 100.000000 % | 0 | 24 | 12271.750956 |
| 2022 | 8760 | 8613 | 98.321918 % | 126 | 20257 | 12142.364343 |
| 2023 | 8760 | 8747 | 99.851598 % | 5 | not_available | 11812.177946 |
| 2024 | 8784 | 8773 | 99.874772 % | 4 | 2 | 11834.389631 |

El consolidado integra 43.848 horas y 43.677 filas completas para d=8. La auditoría contractual de las nueve particiones está en estado PASS.

## Métricas MLP

| d | Partición | Años | n | MAPE (%) | MAE (MW) | RMSE (MW) | Sesgo (MW) |
|---:|---|---|---:|---:|---:|---:|---:|
| 3 | train | 2020-2022 | 26172 | 2.676727 | 37.633106 | 53.246149 | 0.680791 |
| 3 | validation | 2023 | 8752 | 3.904288 | 51.190080 | 65.276283 | 43.032950 |
| 3 | test | 2024 | 8778 | 3.846283 | 51.163020 | 69.165244 | 42.550182 |
| 5 | train | 2020-2022 | 26166 | 4.624036 | 61.981863 | 78.056922 | -28.743231 |
| 5 | validation | 2023 | 8750 | 4.017141 | 52.285857 | 67.872913 | 14.466757 |
| 5 | test | 2024 | 8776 | 4.186405 | 54.748948 | 72.372190 | 11.332332 |
| 8 | train | 2020-2022 | 26157 | 2.884490 | 40.922235 | 56.361396 | -10.782723 |
| 8 | validation | 2023 | 8747 | 3.452548 | 45.309802 | 59.451232 | 32.390678 |
| 8 | test | 2024 | 8773 | 3.426289 | 45.682399 | 62.826471 | 31.772885 |

La configuración seleccionada por validación 2023 es **d=8**, con MAPE **3.452548 %**. Su holdout temporal 2024 obtiene MAPE **3.426289 %**. Todas las dimensiones y particiones cumplen el umbral operativo MAPE ≤35 %.

## Interpretación y limitaciones

- El resultado acredita generalización temporal dentro de la serie HV de Stromnetz Berlin.
- No constituye validación horaria independiente porque entrenamiento, validación y holdout pertenecen al mismo operador y familia de medición.
- Los shares Strombilanz 2020-2023 son anuales y específicos por año; 2024 usa carry-forward 2023 solo para mantener congelado el holdout.
- La normalización temporal 2020-2022 debe revisarse si Stromnetz Berlin confirma una semántica distinta de las etiquetas DST.

## Evidencia detallada

- Auditoría de fuentes: corfo-report/validation/berlin/multiyear_2020_2024/berlin_multiyear_source_audit.md
- Contratos: corfo-report/validation/berlin/multiyear_2020_2024/berlin_multiyear_contract.md
- Auditoría contractual: corfo-report/validation/berlin/multiyear_2020_2024/berlin_multiyear_contract_audit.md
- Métricas completas: corfo-report/validation/berlin/multiyear_2020_2024/berlin_multiyear_model_metrics.csv
- Tabla KPI para resultados: corfo-report/results/tables/berlin_multiyear_expansion_kpi.csv
- Matriz de cumplimiento KPI: corfo-report/results/tables/berlin_multiyear_kpi_compliance.csv
- Figuras de reportabilidad: corfo-report/results/figures/berlin_multiyear_kpi_mape.svg y berlin_multiyear_d8_coverage.svg
- Manifiesto de figuras y hashes: corfo-report/results/figures/berlin_multiyear_reportability_manifest.json
- Postproceso espacial: corfo-report/validation/berlin/multiyear_2020_2024/berlin_multiyear_spatial_postprocess_audit.md
- Mapas anuales: corfo-report/results/figures/berlin_demanda_distrital_multiyear_d8_2020_2024.png y berlin_demanda_distrito_sector_anual_multiyear_d8_2020_2024.png
- Tablas anuales espaciales: corfo-report/results/tables/berlin_multiyear_d8_district_annual.csv y berlin_multiyear_d8_district_sector_annual.csv
