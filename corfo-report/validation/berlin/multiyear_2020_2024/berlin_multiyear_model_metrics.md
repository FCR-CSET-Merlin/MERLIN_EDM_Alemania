# Métricas MLP Berlín multianual 2020-2024

La arquitectura se mantuvo igual al piloto alemán. Se ajustaron los modelos usando 2020-2022, se monitorizó la validación 2023 y se evaluó 2024 una sola vez como holdout temporal congelado. El MAPE no es una validación independiente de fuente: la carga observada sigue siendo HV de Stromnetz Berlin.

| d | Partición | Años | n | MAPE (%) | MAE (MW) | RMSE (MW) | Sesgo (MW) |
|---:|---|---|---:|---:|---:|---:|---:|
| 5 | train | 2020-2022 | 26166 | 4.624036 | 61.981863 | 78.056922 | -28.743231 |
| 5 | validation | 2023 | 8750 | 4.017141 | 52.285857 | 67.872913 | 14.466757 |
| 5 | test | 2024 | 8776 | 4.186405 | 54.748948 | 72.372190 | 11.332332 |
| 8 | train | 2020-2022 | 26157 | 2.884490 | 40.922235 | 56.361396 | -10.782723 |
| 8 | validation | 2023 | 8747 | 3.452548 | 45.309802 | 59.451232 | 32.390678 |
| 8 | test | 2024 | 8773 | 3.426289 | 45.682399 | 62.826471 | 31.772885 |

La selección de d debe hacerse con la validación 2023; el resultado de 2024 debe permanecer reservado para reportar generalización temporal.
