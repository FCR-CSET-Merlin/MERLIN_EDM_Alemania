# Ablación predictiva de rezagos — Berlín 2023

**Estado:** ejecutada como validación temporal interna; el KPI contractual alemán sigue sin declararse.
**Semilla:** `2023`. **Entorno temporal:** Python 3.13.13, TensorFlow 2.21.0, CPU, `TF_NUM_INTRAOP_THREADS=2`, `TF_NUM_INTEROP_THREADS=2`.

## Diseño

Las tres redes se entrenaron desde cero con la misma arquitectura MLP, Huber, Adam, batch 512, máximo 200 épocas, early stopping y el mismo conjunto común de 8.740 horas. Solo cambió el número de rezagos y, por tanto, la dimensión de entrada: `d=3` (19), `d=5` (21) y `d=8` (24).

La partición cronológica fue: entrenamiento 6.118 horas (`2023-01-01T07:00Z` a `2023-09-13T17:00Z`), validación 1.311 (`2023-09-13T18:00Z` a `2023-11-07T08:00Z`) y prueba 1.311 (`2023-11-07T09:00Z` a `2023-12-31T23:00Z`). El escalamiento del objetivo se ajustó solo en entrenamiento.

## Resultados

| Dimensión | Entradas | Épocas | MAPE train (%) | MAPE val. (%) | MAPE prueba (%) | MAE prueba (MW) | RMSE prueba (MW) | Sesgo prueba (MW) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `d=3` | 19 | 129 | 2,068 | 2,752 | **5,089** | **70,4** | **86,5** | -36,9 |
| `d=5` | 21 | 121 | 2,113 | 2,825 | 5,294 | 74,4 | 93,5 | -42,8 |
| `d=8` | 24 | 59 | 2,778 | 3,339 | 5,811 | 81,0 | 103,4 | -42,9 |

En esta partición, `d=3` obtiene el menor MAPE, MAE y RMSE de prueba. Frente a `d=8`, reduce el MAPE de prueba en 0,722 puntos porcentuales. Los tres resultados son inferiores al umbral operativo de 35 %, pero corresponden a un holdout del mismo perfil HV usado para construir el objetivo; por ello se reportan como evidencia preliminar y no como `cumple` contractual.

## Diagnóstico de generalización

El tramo de prueba tiene una carga media observada de 1.443,9 MW, frente a 1.332,6 MW en entrenamiento. Las tres redes subestiman ese tramo: el sesgo es -36,9 MW para `d=3`, -42,8 MW para `d=5` y -42,9 MW para `d=8`. La diferencia entre MAPE de entrenamiento y prueba es 3,021, 3,180 y 3,033 puntos porcentuales, respectivamente. Esto muestra un cambio temporal de nivel/estacionalidad y no permite atribuir la diferencia exclusivamente a overfitting.

La evidencia favorece provisionalmente `d=3` para Berlín 2023. Antes de fijarlo como configuración definitiva se debe repetir con otra semilla, otro año o una ventana de prueba adicional y cerrar los shares C/P y `region_comuna_share`.

## Artefactos y reproducibilidad

- Índice de métricas y hashes: [`lag_ablation_predictiva_2023.csv`](../berlin/lag_ablation_predictiva_2023.csv).
- Contratos de entrada: [`contrato_entrenamiento_berlin_2023.md`](contrato_entrenamiento_berlin_2023.md).
- Entrenador: [`train_mlp_berlin.py`](../../prototipo_3/src/train_mlp_berlin.py).
- Pesos y JSON de resultados: bajo `prototipo_3/data/de_alemania/berlin_training_2023/model_d{3,5,8}/`, fuera de Git, identificados por hash en el índice.

Ejemplo de repetición para una dimensión:

```bash
PYTHONPATH=/tmp/merlin_tf_deps:/tmp/merlin_de_deps \
python prototipo_3/src/train_mlp_berlin.py --dimension 3 \
  --data-root prototipo_3/data/de_alemania/berlin_training_2023
```
