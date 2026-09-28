# Registro de avance — adaptación de MERLIN EDM a Alemania

**Caso:** reconstrucción histórica de demanda eléctrica de Berlín
**Fecha de corte:** 21 de septiembre de 2026
**Repositorio:** `MERLIN_EDM_Alemania`
**Rama:** `germany/main`
**Estado global:** **Fase 0 en curso**. No se ha ejecutado el modelo alemán ni se ha evaluado el KPI.

Este archivo es la bitácora operativa del [plan de trabajo](../../PLAN_TRABAJO_ADAPTACION_ALEMANIA.md). Se actualizará en cada hito con fecha, evidencia, decisión y siguiente acción. Un estado no cambia a `cerrado` sin el producto y los criterios de aceptación de la fase.

## Estado por fase

| Fase | Estado | Avance verificable | Evidencia | Criterio de cierre |
|---|---|---|---|---|
| Fase 0 — Factibilidad y contrato de datos | **En curso** | HV 2019–2023 y Strombilanz 2023 auditadas; perímetro `11000`; HV 2023 normalizada a 15 min y hora; DWD Tempelhof y tabla integrada con ocho rezagos preparados; alcance HV, timestamps y cartografía siguen pendientes | [Auditoría HV 2019–2023](sources/stromnetz_berlin_hv_2019_2023_auditoria.md), [normalización HV](sources/normalizacion_temporal_hv_2023.md), [auditoría DWD](sources/dwd_berlin_tempelhof_2023_auditoria.md), [tabla integrada](sources/berlin_hv_temperature_features_2023.md), [solicitud enviada](sources/solicitud_stromnetz_berlin_perimetro_y_semantica.md) | Semántica general y referencias anuales verificadas; contrato HV, sectores y variables alemanas requiere cierre; dictamen GO/GO condicionado/NO-GO |
| Fase 1 — Homologación territorial, sectorial y temporal | **En curso** | FNN climático provisional ejecutado con `tau=1`; tablas comparables para `d=3`, `d=5` y `d=8` preparadas; contrato sectorial y territorial aún no cerrado | [Diagnóstico FNN](sources/fnn_berlin_temperature_2023.md), [ablación de rezagos](sources/lag_ablation_berlin_2023.md), [contrato de entrenamiento](sources/contrato_entrenamiento_berlin_2023.md) | Correspondencias de red, Berlín, distritos y sectores; unidades, DST y selección predictiva de rezagos verificadas |
| Fase 2 — Línea base y adaptación | **En curso** | Contrato alemán parametrizado y ablación TensorFlow ejecutada para `d=3`, `d=5` y `d=8`; `d=3` obtiene el menor MAPE de prueba (5,089 %); shares C/P y `region_comuna_share` siguen provisionales | [Contrato de entrenamiento](sources/contrato_entrenamiento_berlin_2023.md), [ablación predictiva](sources/lag_ablation_predictiva_berlin_2023.md), [entrenador alemán](../../prototipo_3/src/train_mlp_berlin.py) | Modelo, columnas, scaler, entorno y diferencias Chile–Alemania identificados; selección de rezagos estable en validaciones adicionales |
| Fase 3 — Reconstrucción histórica de Berlín | Pendiente | Insumos HV, temperatura y tabla integrada generados; no hay inferencia ni tablas de resultados | [Series](../results/timeseries/README.md) | Corrida reproducible con cobertura, perímetro y hashes |
| Fase 4 — Validación y KPI | Pendiente | KPI alemán no evaluado | [Plan KPI](kpi_plan.md), [cumplimiento](cumplimiento_kpi.md) | CSV KPI, resumen, ficha y manifiesto revisados |
| Fase 5 — Escalamiento territorial | Pendiente | No iniciada | — | Piloto Berlín cerrado y reproducible |

## Estado de fuentes

| Grupo | Estado | Decisión actual |
|---|---|---|
| Stromnetz Berlin — categorías y HV 2019–2023 | **GO condicionado para el piloto** | Perfiles HV 2019–2023 completos en valores; HV es candidato principal, niveles no sumables; semántica de Lastgang confirmada y alcance HV/timestamps en revisión; se usa `11000` como referencia y HV como proxy |
| Statistik Berlin-Brandenburg | **Aceptada como referencia anual** | Edición corregida 2023 auditada; consumo final total/sectorial independiente de HV; usar para consistencia anual condicionada |
| Umweltatlas Berlin | Candidata espacial | Revisar cobertura distrital, privacidad y año de referencia |
| DWD Berlin-Tempelhof 00433 | **Seleccionada condicionada para primera corrida** | 8.760 horas 2023; cinco faltantes explícitos; usar casos completos y revisar representatividad espacial |
| VG250/Zensus/Destatis/BA | Covariables y límites | VG250 `11000` aceptado para el perímetro piloto; las demás covariables se incorporan tras completar el contrato territorial |
| SMARD/BDEW/DemandRegio | Contexto o prior | No usar como comparador independiente sin auditoría específica |

Los estados anteriores indican factibilidad potencial, no aceptación de datos. La ficha completa se conservará en `validation/sources/`.

## KPI

- **Meta operativa:** MAPE ≤35 %.
- **Estado:** no evaluado.
- **Comparador horario:** pendiente de confirmar una serie de red independiente.
- **Comparador anual/sectorial:** Strombilanz 2023 auditada; uso condicionado como control de escala.
- **Regla:** si el balance se usa para shares o escalamiento, la comparación contra él se etiqueta como consistencia condicionada.

No se publicará `cumple` hasta que exista una fila en `kpi_validation.csv`, una explicación en `cumplimiento_kpi.md`, una ficha firmada/revisada y un manifiesto reproducible.

## Próximas acciones

1. Registrar la respuesta de Stromnetz Berlin cuando llegue y actualizar el dictamen semántico, temporal y cartográfico.
2. Resolver el tratamiento de las 20 filas sin ocho temperaturas válidas y documentar la política de casos completos.
3. Sustituir los shares sectoriales provisionales por una separación alemana defendible de GHD y público, y cerrar la interpretación de `region_comuna_share`.
4. Repetir la ablación con otra semilla, año o ventana temporal para verificar si la ventaja de `d=3` es estable.
5. Fijar el entorno TensorFlow 2.21.0 usado en la corrida y conservar los pesos/resultados por dimensión con sus hashes.
6. Ejecutar una línea base de reconstrucción sobre 2023, sin declarar todavía cumplimiento del KPI.
7. Comparar los perfiles HV 2019–2023 una vez resuelto el contrato temporal y registrar cambios de metodología.

## Bitácora

| Fecha | Fase | Acción / decisión | Resultado | Evidencia |
|---|---|---|---|---|
| 2026-09-21 | Preparación | Se creó la reportabilidad alemana, se separó la referencia chilena y se publicó el plan de adaptación | Commit `c951f09`; estructura lista | [Reportabilidad](../README.md), [plan](../../PLAN_TRABAJO_ADAPTACION_ALEMANIA.md) |
| 2026-09-21 | Fase 0 | Se inicializó este registro de avance | Fase 0 marcada como `En curso`; no se declara KPI | Este archivo |
| 2026-09-21 | Fase 0 | Se descargó y auditó Restlast SLP 2023 | 35.040 intervalos completos; GO condicionado para SLP, no demanda total | [Auditoría SLP](sources/stromnetz_berlin_restlast_2023.md) |
| 2026-09-21 | Fase 0 | Se auditaron perfiles HV, HV/MV, MV, MV/LV, LV, pérdidas y pronóstico SLP 2023 | HV es candidato anual principal; perfiles jerárquicos no sumables; se fijó Berlín administrativo `11000` como perímetro operativo y HV como proxy; 1.046,64 km² queda como métrica regulatoria separada | [Categorías y perímetro](sources/stromnetz_berlin_categorias_perimetro_2023.md), [decisión territorial](sources/decision_perimetro_berlin.md) |
| 2026-09-21 | Fase 0 | Se auditó la Strombilanz oficial corregida de Berlín 2023 y se comparó con HV 2020–2023 | Consumo final 2023: 11.780 GWh; diferencia HV–EEV 2023: +0,273 %; referencia aceptada para consistencia anual condicionada | [Auditoría Strombilanz](sources/statistik_berlin_strombilanz_2023_auditoria.md) |
| 2026-09-21 | Fase 0 | Se probó la normalización temporal de HV 2023 | 35.040 instantes UTC únicos con paso de 15 minutos; 2 diferencias de etiqueta local en las transiciones DST; especificación aceptada para el piloto | [Normalización temporal HV 2023](sources/normalizacion_temporal_hv_2023.md) |
| 2026-09-21 | Fase 0 | Se auditaron los perfiles HV 2019–2023 y la documentación semántica oficial | Valores, máximos y energía anual consistentes; se detectaron anomalías de timestamps 2020–2022 y queda pendiente confirmar alcance HV y cartografía; solicitud enviada; se espera respuesta | [Auditoría HV 2019–2023](sources/stromnetz_berlin_hv_2019_2023_auditoria.md), [solicitud enviada](sources/solicitud_stromnetz_berlin_perimetro_y_semantica.md) |
| 2026-09-28 | Fase 0 | Se generaron las series HV 2023 normalizada y horaria con preprocesador estándar | 35.040 intervalos; 8.760 horas; 11.812.177,946 MWh; 2 etiquetas DST discrepantes marcadas; artefactos pesados ignorados por Git | [Índice de series](../results/timeseries/berlin_inputs_2023_index.csv), [preprocesador HV](../../prototipo_3/preprocessing/berlin_hv_2023.py) |

| 2026-09-28 | Fase 0 | Se extrajo DWD Berlin-Tempelhof y se integró con HV mediante ocho rezagos UTC | 8.760 horas climáticas; 5 faltantes DWD; 8.740 filas completas para la tabla integrada; no se imputaron valores | [Auditoría DWD](sources/dwd_berlin_tempelhof_2023_auditoria.md), [tabla integrada](sources/berlin_hv_temperature_features_2023.md) |

| 2026-09-28 | Fase 1 | Se ejecutó FNN provisional sobre DWD Berlin-Tempelhof con `tau=1` hora | Con `R=10`, primera dimensión bajo 1 %: `d=5` (4 rezagos); con `R=30`: `d=3` (2 rezagos); se usaron dos segmentos continuos sin imputación y se mantiene `d=8` provisional hasta la ablación predictiva | [Diagnóstico FNN](sources/fnn_berlin_temperature_2023.md) |
| 2026-09-28 | Fase 1 | Se prepararon las tablas comparables para la ablación predictiva de rezagos | `d=3`: 8.750 filas propias; `d=5`: 8.746; `d=8`: 8.740; conjunto común: 8.740 horas; no se imputaron temperaturas | [Ablación de rezagos](sources/lag_ablation_berlin_2023.md), [índice](berlin/lag_ablation_2023_index.csv) |
| 2026-09-28 | Fase 2 | Se adaptó el contrato de entrenamiento chileno al piloto alemán | Generadores `d=3/d=5/d=8` con 19/21/24 entradas; cada contrato usa 6.118 horas de entrenamiento, 1.311 de validación y 1.311 de prueba; modo seco validado; shares C/P provisionales | [Contrato alemán](sources/contrato_entrenamiento_berlin_2023.md), [índice Parquet](berlin/berlin_training_contract_2023_index.csv), [entrenador](../../prototipo_3/src/train_mlp_berlin.py) |
| 2026-09-28 | Fase 2 | Se ejecutó la ablación predictiva sobre el conjunto común | MAPE de prueba: `d=3` 5,089 %; `d=5` 5,294 %; `d=8` 5,811 %; `d=3` es la mejor configuración preliminar; no se declara KPI contractual | [Ablación predictiva](sources/lag_ablation_predictiva_berlin_2023.md), [índice de métricas](berlin/lag_ablation_predictiva_2023.csv) |

## Regla de actualización

Cada modificación futura debe añadir una fila a la bitácora y actualizar la tabla de fases. La entrada debe indicar qué evidencia nueva se generó, qué decisión se tomó, qué limitación permanece y cuál es la siguiente acción. No se deben borrar estados anteriores ni reemplazar resultados desfavorables por versiones favorables.
