# Diagnóstico FNN de temperatura — Berlín 2023

**Estado:** diagnóstico provisional; no define todavía el número final de entradas del MLP.  
**Serie:** DWD Berlin-Tempelhof, estación `00433`, 2023.  
**Observaciones válidas:** 8.755; el cálculo FNN utilizó 8.754 observaciones en dos segmentos horarios continuos y excluyó 5 faltantes sin imputación más un segmento aislado de una observación.  
**Implementación:** `nolitsa.dimension.fnn`, ejecución secuencial (`parallel=False`). Entorno temporal: Python 3.13.13, Nolitsa 0.1, NumPy 2.5.3, SciPy 1.18.1 y Numba 0.67.0.

## Configuración común

- `tau = 1` hora, para mantener la estructura temporal del modelo chileno.
- Dimensiones evaluadas: `d = 1, ..., 15`.
- Ventana de Theiler: 10 muestras.
- `A = 2` para el Test II.
- `maxnum = 100`, necesario porque la temperatura está redondeada a 0,1 °C y contiene vecinos con distancia cero.
- Los faltantes dividen la serie en segmentos; no se concatenan horas separadas ni se interpola.
- Umbral diagnóstico: fracción FNN ≤ 1 %.

`tau=1` significa que una dimensión `d` contiene la temperatura actual y valores separados cada una hora. Por ejemplo, `d=5` equivale a `t, t-1, ..., t-4`: cuatro rezagos además de la observación contemporánea.

## Sensibilidad al parámetro R

| Configuración | Primera dimensión con Test I ≤1 % | Rezagos equivalentes | Fracción en esa dimensión | Archivo |
|---|---:|---:|---:|---|
| `R=10` (predeterminado efectivo de Nolitsa) | **5** | 4 | 0,309 % | [CSV](../berlin/fnn_temperature_2023.csv) · [manifiesto](../berlin/fnn_temperature_2023.json) |
| `R=30` (valor declarado, pero no aplicado en el notebook chileno) | **3** | 2 | 0,389 % | [CSV](../berlin/fnn_temperature_2023_R30.csv) · [manifiesto](../berlin/fnn_temperature_2023_R30.json) |

El Test II presentó fracciones inferiores a 0,2 % en las dimensiones evaluadas; el primer umbral combinado coincide con el resultado del Test I.

## Interpretación

El diagnóstico indica que, para esta estación y este año, una representación de 2–4 rezagos horarios elimina la mayor parte de los vecinos falsos bajo un umbral de 1 %. La configuración heredada de Chile (`d=8`, temperatura contemporánea más siete rezagos) es más conservadora que ambas alternativas, pero sigue siendo técnicamente posible.

El resultado es sensible a `R` y se obtuvo con una única estación y un solo año. FNN estima una dimensión de embedding de la temperatura; no estima directamente qué columnas minimizan el error de demanda. Por ello, este resultado no permite declarar que `d=3` o `d=5` sea óptimo para la red.

## Decisión provisional

- Mantener `tau=1` hora.
- Conservar `d=8` durante la primera línea base para aislar el efecto de la adaptación territorial y sectorial.
- Ejecutar después una ablación predictiva con `d=3`, `d=5` y `d=8`, usando exactamente la misma división temporal y comparando MAPE, MAE, RMSE, sesgo energético y estabilidad estacional.
- Reportar el valor de `R`, `A`, ventana de Theiler, faltantes y versión de Nolitsa en cada corrida.

La selección definitiva de rezagos se hará con validación temporal de la demanda HV, no con FNN por sí solo.
