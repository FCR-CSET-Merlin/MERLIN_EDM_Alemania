# Inferencia horaria Berlín 2023 — contrato d=3

La salida corresponde a la red MLP alemana d=3 entrenada con el contrato cronológico 2023. Se reconstruyen únicamente las horas con temperatura contemporánea y dos rezagos disponibles; no se imputan las 20 horas faltantes.

- Filas exportadas: **8740 de 8760** (99.771689 %).
- Cobertura: **20 horas no exportadas** por completitud de features d=3.
- Energía observada en filas completas: **11784.781238 GWh**; predicha: **11738.062673 GWh**.
- MAPE test interno HV: **5.089161 %**; umbral operativo: **35 %**.
- MAE test: **70.395301 MW**; RMSE test: **86.549150 MW**; sesgo test: **-36.899373 MW**.

La fila formal del KPI está en [`../kpi_validation.csv`](../kpi_validation.csv).

## Alcance de validación

El MAPE es una validación interna sobre el mismo perfil HV de Stromnetz Berlin utilizado como objetivo del entrenamiento y su partición temporal de test. Por tanto, acredita el desempeño de reconstrucción interna del piloto, pero no constituye todavía una validación horaria externa independiente.

La tabla de filas y el manifiesto reproducible se mantienen en el área de datos ignorada; este resumen y la tabla de métricas son la evidencia reportable.
