# Auditoría de temperatura DWD — Berlin-Tempelhof 2023

**Estado:** seleccionada para la primera corrida climática, condicionada a control de faltantes y representatividad espacial.  
**Estación:** DWD `00433`, Berlin-Tempelhof.  
**Fuente:** [DWD CDC — observaciones horarias de temperatura del aire](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/air_temperature/historical/).  
**Descripción metodológica:** [dataset description](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/air_temperature/DESCRIPTION_obsgermany_climate_hourly_air_temperature_en.pdf).  
**Archivo descargado:** `stundenwerte_TU_00433_19510101_20251231_hist.zip`.  
**SHA-256 del ZIP:** `ee67c7cf45b820ff3c28ac579fc3d3ce790ca41468709a45bd30ad8717de1267`

## Selección de la estación

El catálogo DWD informa para 2023:

| Campo | Valor |
|---|---:|
| Código | `00433` |
| Nombre | Berlin-Tempelhof |
| Latitud | 52,4676 |
| Longitud | 13,4020 |
| Elevación | 47,74 m |
| Cobertura histórica | 1951–2025 en el archivo descargado |

La estación se usa como primera aproximación de temperatura urbana para Berlín. No se afirma que represente todos los microclimas del territorio; esa sensibilidad se revisará posteriormente con ERA5-Land o estaciones adicionales.

## Variable y tiempo

Se extrajo `TT_TU`, temperatura del aire en °C. La metadata de la estación indica que desde el 01-04-2001 los valores se expresan en UTC; por tanto, para 2023 se conserva `timestamp_utc` como llave de unión y `timestamp_local` solo para presentación en `Europe/Berlin`.

El archivo resultante mantiene el indicador de calidad `QN_9` y convierte el código DWD `-999` en valor vacío con una bandera explícita. No se realizó imputación.

## Cobertura observada

| Control | Resultado |
|---|---:|
| Horas esperadas | 8.760 |
| Horas extraídas | 8.760 |
| Primer instante UTC | `2023-01-01T00:00:00+00:00` |
| Último instante UTC | `2023-12-31T23:00:00+00:00` |
| Observaciones faltantes | 5 |
| Fechas faltantes | 03-04-2023 06:00, 07:00, 08:00, 09:00 y 11:00 UTC |
| Salida | `prototipo_3/data/de_alemania/berlin_temperature_2023/berlin_tempelhof_2023_hourly.csv` |
| SHA-256 salida | `fee8ce844791e12a78d9da25c4c99934a82a327bb77b3ece890eb954f61ee4b4` |

## Dictamen de uso

La fuente es apta para la primera corrida climática con tratamiento de casos completos. No se rellenan faltantes hasta comparar el efecto de una imputación contra una corrida sin imputar. La tabla integrada con la carga HV contiene 8.740 filas completas para la temperatura contemporánea y sus siete rezagos; las 20 filas incompletas quedan identificadas y excluidas de cualquier entrenamiento que exija ocho valores válidos.
