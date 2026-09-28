# Preparación de ablación de rezagos — Berlín 2023

**Estado:** tablas comparables preparadas; el MLP aún no se ha ejecutado.  
**Configuraciones:** `d=3`, `d=5` y `d=8`, siempre con `tau=1` hora.  
**Política:** no imputar temperaturas; cada configuración usa casos completos y se conserva además una intersección común para comparar exactamente las mismas horas.

## Cobertura

| Configuración | Temperaturas incluidas | Filas completas propias | Filas en conjunto común |
|---|---|---:|---:|
| `d=3` | `t` a `t-2` | 8.750 | 8.740 |
| `d=5` | `t` a `t-4` | 8.746 | 8.740 |
| `d=8` | `t` a `t-7` | 8.740 | 8.740 |

El conjunto común usa exactamente las 8.740 horas válidas para `d=8`, evitando que una configuración obtenga ventaja por contar con más observaciones. Las tablas específicas permiten, como análisis secundario, medir el efecto de la cobertura.

## Contrato de comparación

Las tres configuraciones comparten:

- misma serie HV horaria y misma llave `timestamp_hour_end_utc`;
- mismo DWD Berlin-Tempelhof y misma política de faltantes;
- mismas variables de calendario local `Europe/Berlin`;
- mismo perímetro proxy y misma fuente de demanda;
- mismo particionamiento temporal, escalamiento ajustado solo en entrenamiento y semilla de la red.

Solo cambia el número de columnas de temperatura. La ablación deberá informar MAPE, MAE, RMSE, sesgo energético, estabilidad estacional y diferencia entre entrenamiento y validación.

## Artefactos

El índice con hashes se encuentra en [`lag_ablation_2023_index.csv`](../berlin/lag_ablation_2023_index.csv). Los archivos de datos permanecen bajo `prototipo_3/data/de_alemania/berlin_lag_ablation_2023/` y están excluidos de Git. El generador reproducible es [`berlin_lag_ablation_2023.py`](../../prototipo_3/preprocessing/berlin_lag_ablation_2023.py).

Esta preparación no fija el número definitivo de rezagos. La selección se hará después de observar el desempeño predictivo de la red.
