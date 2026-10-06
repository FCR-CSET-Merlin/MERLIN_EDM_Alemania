# Shares sectoriales anuales multianuales de Berlín

Fuente: Strombilanz corregida, hoja S.28_Strombilanz, XLSX prototipo_3/data/de_alemania/external_validation/berlin_2023/SB_E04-04-00_2023j01_BE.xlsx.
SHA-256 de la fuente: 5b9acbf60a48526c5a25c2a92f8343a9387327071e69418918bded08b7031cce.

Los años 2020-2023 se extraen del bloque de consumo final de la tabla S.28. El sector público permanece en cero porque la fuente no lo separa. La fila 2024 conserva los shares 2023 únicamente para permitir un holdout con variables congeladas; no es un dato observado de Strombilanz 2024.

| Año | Año fuente | Total GWh | Industria | Residencial | GHD | Transporte | Público | Estado |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2020 | 2020 | 12367.796000000 | 0.115362429975 | 0.341766067293 | 0.475115291358 | 0.067756211373 | 0.000000000000 | observed_annual |
| 2021 | 2021 | 12359.425000000 | 0.119045263028 | 0.333869415446 | 0.474954296013 | 0.072131025513 | 0.000000000000 | observed_annual |
| 2022 | 2022 | 12200.846000000 | 0.113053963635 | 0.330192594841 | 0.485162340382 | 0.071591101142 | 0.000000000000 | observed_annual |
| 2023 | 2023 | 11780.229000000 | 0.109844553956 | 0.336635815823 | 0.476132255154 | 0.077387375067 | 0.000000000000 | observed_annual |
| 2024 | 2023 | 11780.229000000 | 0.109844553956 | 0.336635815823 | 0.476132255154 | 0.077387375067 | 0.000000000000 | frozen_last_available_for_holdout_only |

Salida: corfo-report/validation/berlin/berlin_sector_shares_multiyear_2020_2024.csv.
La tabla está lista para alimentar el contrato multianual, sujeto a la auditoría temporal HV y a la decisión de no usar la fila 2024 como evidencia sectorial independiente.
