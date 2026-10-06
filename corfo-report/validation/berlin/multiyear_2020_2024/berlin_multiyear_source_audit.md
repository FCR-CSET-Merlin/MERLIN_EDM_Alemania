# Auditoría de fuentes multianuales Berlín 2020-2024

Esta entrega prepara la expansión temporal sin crear todavía un contrato de entrenamiento. La serie HV se normaliza a UTC y la temperatura DWD se une con rezagos causales de 0-7 horas.

## Regla temporal

Los CSV HV crudos se recorren en el orden publicado. Se genera el primer timestamp UTC a partir de 01-01 00:15 de Europe/Berlin y se incrementa cada 15 minutos. Esto evita corregir manualmente los errores de fecha 2020-2022, conserva todos los valores y registra las discrepancias frente a las etiquetas locales. La hora UTC es el índice canónico y no se elimina la hora repetida por DST.

## Cobertura auditada


| Año | Horas HV | Cuartos de hora | Desajustes de etiqueta | UTC continuo | Horas con 8 rezagos térmicos | Cobertura térmica | Energía calculada (GWh) | Comparación con fuente |
|---:|---:|---:|---:|:---:|---:|---:|---:|---:|
| 2020 | 8784 | 35136 | 20166 | True | 8784 | 100.000000000 % | 12247.204539750 | -0.000000002 % |
| 2021 | 8760 | 35040 | 24 | True | 8760 | 100.000000000 % | 12271.750956000 | 0.000000000 % |
| 2022 | 8760 | 35040 | 20257 | True | 8613 | 98.321917808 % | 12142.364343000 | 0.000000000 % |
| 2023 | 8760 | not_available | not_available | True | 8747 | 99.851598174 % | 11812.177946000 |  |
| 2024 | 8784 | 35136 | 2 | True | 8773 | 99.874772313 % | 11834.389631250 | 0.000000002 % |

## Dictamen de integración

- La tabla horaria multianual queda disponible para auditoría; los valores HV no fueron imputados ni corregidos manualmente.
- 2020-2022 deben considerarse años con riesgo temporal documentado hasta recibir confirmación del operador sobre las etiquetas DST.
- El DWD histórico cubre los años solicitados; los faltantes se mantienen explícitos y las filas incompletas no se usarán en un contrato de entrenamiento.
- La expansión aún no tiene GO para entrenar: faltan shares sectoriales anuales homologados para cada año. El siguiente control es auditar Strombilanz 2020-2024 y construir el contrato con entrenamiento 2020-2022, validación 2023 y holdout 2024.

Artefacto integrado: prototipo_3/data/de_alemania/berlin_multiyear/berlin_hv_temperature_features_2020_2024.csv (SHA-256 0f99a0bc24f584e7b937749470452ab08336eba607139b33fcf7feb6e581383c).
Manifiesto: prototipo_3/data/de_alemania/berlin_multiyear/berlin_multiyear_features_manifest.json.
