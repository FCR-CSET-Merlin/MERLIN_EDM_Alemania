# Auditoría del contrato Berlín multianual

Estado global: **PASS**.

Se verificaron columnas, valores finitos, suma de shares, correspondencia con los shares anuales permitidos y objetivo escalado. La partición se mantiene por años completos y el holdout 2024 usa la fila marcada como carry-forward 2023.

| d | Partición | Filas | Columnas | Finitud | Shares | Error suma | Media target train | Estado |
|---:|---|---:|:---:|:---:|:---:|---:|---:|:---:|
| 3 | train | 26172 | True | True | True | 1.000e-12 | 8.47047736349e-17 | pass |
| 3 | validation | 8752 | True | True | True | 0.000e+00 | -0.147289433306 | pass |
| 3 | test | 8778 | True | True | True | 0.000e+00 | -0.15073933271 | pass |
| 5 | train | 26166 | True | True | True | 1.000e-12 | 4.6055204458e-16 | pass |
| 5 | validation | 8750 | True | True | True | 0.000e+00 | -0.147311140547 | pass |
| 5 | test | 8776 | True | True | True | 0.000e+00 | -0.150715996393 | pass |
| 8 | train | 26157 | True | True | True | 1.000e-12 | 2.73818510397e-16 | pass |
| 8 | validation | 8747 | True | True | True | 0.000e+00 | -0.147413960344 | pass |
| 8 | test | 8773 | True | True | True | 0.000e+00 | -0.150728036899 | pass |

El resultado no evalúa el MAPE: solo acredita la integridad del contrato antes del reentrenamiento.
