# Contrato de entrenamiento Berlín multianual 2020-2024

Se generaron contratos independientes para d=3, d=5 y d=8. La partición es cronológica por año: entrenamiento 2020-2022, validación 2023 y prueba/holdout 2024. El scaler se ajustó únicamente con el entrenamiento. Los shares son anuales; la fila 2024 está etiquetada como carry-forward 2023 para holdout.

| d | Partición | Años | Filas | mu train (MW) | sigma train (MW) |
|---:|---|---|---:|---:|---:|
| 3 | train | 2020,2021,2022 | 26172 | 1393.710895776020 | 309.047605111226 |
| 3 | validation | 2023 | 8752 | 1393.710895776020 | 309.047605111226 |
| 3 | test | 2024 | 8778 | 1393.710895776020 | 309.047605111226 |
| 5 | train | 2020,2021,2022 | 26166 | 1393.664223935642 | 309.067493048817 |
| 5 | validation | 2023 | 8750 | 1393.664223935642 | 309.067493048817 |
| 5 | test | 2024 | 8776 | 1393.664223935642 | 309.067493048817 |
| 8 | train | 2020,2021,2022 | 26157 | 1393.587503020224 | 309.092614867246 |
| 8 | validation | 2023 | 8747 | 1393.587503020224 | 309.092614867246 |
| 8 | test | 2024 | 8773 | 1393.587503020224 | 309.092614867246 |

Los Parquet están bajo prototipo_3/data y permanecen fuera de Git por su regla de exclusión. Antes de entrenar se debe ejecutar la auditoría de columnas, shares y cobertura, y mantener 2024 congelado como holdout.
