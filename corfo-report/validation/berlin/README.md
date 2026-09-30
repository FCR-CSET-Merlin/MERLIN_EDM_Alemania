# Validación del piloto Berlín

Esta carpeta reunirá los informes por corrida y año del caso alemán. Cada informe debe identificar perímetro (Berlín administrativo o área de Stromnetz Berlin), zona horaria, cobertura, fuentes, modelo, commit y criterio KPI.

La inferencia alemana d=3 ya fue exportada y el KPI horario interno está calculado (MAPE test 5,089161454 %). La validación horaria externa y el KPI espacial independiente siguen pendientes. El diagnóstico FNN climático provisional está en [fnn_berlin_temperature_2023.md](../sources/fnn_berlin_temperature_2023.md).

También están preparadas las tablas comparables para la ablación predictiva de `d=3`, `d=5` y `d=8` en [lag_ablation_berlin_2023.md](../sources/lag_ablation_berlin_2023.md); estos artefactos fueron el insumo para seleccionar d=3; la evidencia de inferencia está en [inference_2023/berlin_d3_inference_2023_summary.md](inference_2023/berlin_d3_inference_2023_summary.md).

El [contrato de entrenamiento alemán](../sources/contrato_entrenamiento_berlin_2023.md) ya genera Parquet compatibles con el entrenador para las tres dimensiones. La [ablación predictiva](../sources/lag_ablation_predictiva_berlin_2023.md) fue ejecutada como validación temporal interna; todavía no constituye evidencia KPI contractual independiente.


El postproceso distrito–sector de la inferencia d=3 está disponible en [la auditoría de conservación](inference_2023/berlin_district_sector_d3_2023_audit.md). Incluye una tabla horaria larga comprimida de 524.400 filas (`.csv.gz`), tablas anuales por distrito y sector, un resumen horario por sector y mapas anual y de la hora de máxima demanda predicha. Los resultados usan `annual_broadcast` y se clasifican como asignación condicionada; no son observaciones independientes ni KPI espacial/sectorial.
