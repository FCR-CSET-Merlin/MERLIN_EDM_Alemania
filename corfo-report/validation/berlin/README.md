# Validación del piloto Berlín

Esta carpeta reunirá los informes por corrida y año del caso alemán. Cada informe debe identificar perímetro (Berlín administrativo o área de Stromnetz Berlin), zona horaria, cobertura, fuentes, modelo, commit y criterio KPI.

No hay una corrida de reconstrucción alemana ni un KPI calculado. Ya existe un diagnóstico FNN climático provisional en [fnn_berlin_temperature_2023.md](../sources/fnn_berlin_temperature_2023.md).

También están preparadas las tablas comparables para la ablación predictiva de `d=3`, `d=5` y `d=8` en [lag_ablation_berlin_2023.md](../sources/lag_ablation_berlin_2023.md); estos artefactos aún no constituyen resultados del modelo ni evidencia de KPI.

El [contrato de entrenamiento alemán](../sources/contrato_entrenamiento_berlin_2023.md) ya genera Parquet compatibles con el entrenador para las tres dimensiones. El entrenamiento TensorFlow aún no se ha ejecutado.
