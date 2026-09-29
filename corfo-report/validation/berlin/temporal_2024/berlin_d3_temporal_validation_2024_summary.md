# Validación temporal Berlín 2024 — modelo d=3 congelado

Se aplicó sin reentrenamiento el modelo d=3 ajustado con 2023. Se conservaron la arquitectura, las 19 variables, el scaler y los shares sectoriales 2023. El resultado mide generalización temporal dentro de la serie HV del mismo operador; no es validación independiente de fuente.

- Cobertura: **8776/8784 horas** (99.908925 %); horas no imputadas: **8**.
- MAPE: **3.095866 %**.
- MAE: **41.850056 MW**; RMSE: **57.472507 MW**; sesgo: **-4.673725 MW**.
- Energía observada en filas completas: **11822.880648 GWh**; predicha: **11781.864037 GWh**.
- Error de punta: **-2.494640 %**.
- Etiquetas de hora local duplicadas por DST: **1**; índice canónico: UTC.

## Interpretación para KPI

Este resultado puede reportarse como validación fuera de muestra temporal (`comparador_independiente=no`, `dependencia_input=si` respecto del operador y de la familia HV). No debe presentarse como una validación externa independiente de Berlín. La validación de fuente independiente queda `no_evaluable` mientras no exista una serie horaria medida con perímetro compatible y procedencia distinta.
