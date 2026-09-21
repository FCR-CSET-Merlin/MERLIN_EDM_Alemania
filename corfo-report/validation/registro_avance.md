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
| Fase 0 — Factibilidad y contrato de datos | **En curso** | Categorías 2019–2023 y Strombilanz 2023 auditadas; perímetro operativo fijado como Berlín administrativo `11000`; semántica general de Lastgang confirmada; alcance HV, timestamps y cartografía siguen pendientes | [Auditoría de categorías y perímetro](sources/stromnetz_berlin_categorias_perimetro_2023.md), [auditoría HV 2019–2023](sources/stromnetz_berlin_hv_2019_2023_auditoria.md), [decisión territorial](sources/decision_perimetro_berlin.md), [solicitud enviada](sources/solicitud_stromnetz_berlin_perimetro_y_semantica.md), [inventario](sources/inventario_fuentes.csv) | Semántica general de Lastgang y referencia anual verificadas; alcance HV, timestamps y cartografía requieren respuesta/normalización; dictamen GO/GO condicionado/NO-GO |
| Fase 1 — Homologación territorial, sectorial y temporal | Pendiente | Sin contrato alemán validado | — | Correspondencias de red, Berlín, distritos y sectores; unidades y DST verificadas |
| Fase 2 — Línea base y adaptación | Pendiente | No hay ejecución del modelo alemán | — | Modelo, columnas, scaler, entorno y diferencias Chile–Alemania identificados |
| Fase 3 — Reconstrucción histórica de Berlín | Pendiente | No hay series ni tablas alemanas generadas | [Series](../results/timeseries/README.md) | Corrida reproducible con cobertura, perímetro y hashes |
| Fase 4 — Validación y KPI | Pendiente | KPI alemán no evaluado | [Plan KPI](kpi_plan.md), [cumplimiento](cumplimiento_kpi.md) | CSV KPI, resumen, ficha y manifiesto revisados |
| Fase 5 — Escalamiento territorial | Pendiente | No iniciada | — | Piloto Berlín cerrado y reproducible |

## Estado de fuentes

| Grupo | Estado | Decisión actual |
|---|---|---|
| Stromnetz Berlin — categorías y HV 2019–2023 | **GO condicionado para el piloto** | Perfiles HV 2019–2023 completos en valores; HV es candidato principal, niveles no sumables; semántica de Lastgang confirmada y alcance HV/timestamps en revisión; se usa `11000` como referencia y HV como proxy |
| Statistik Berlin-Brandenburg | **Aceptada como referencia anual** | Edición corregida 2023 auditada; consumo final total/sectorial independiente de HV; usar para consistencia anual condicionada |
| Umweltatlas Berlin | Candidata espacial | Revisar cobertura distrital, privacidad y año de referencia |
| DWD/ERA5-Land | Candidata climática | Seleccionar fuente, versión y tratamiento horario |
| VG250/Zensus/Destatis/BA | Covariables y límites | VG250 `11000` aceptado para el perímetro piloto; las demás covariables se incorporan tras completar el contrato territorial |
| SMARD/BDEW/DemandRegio | Contexto o prior | No usar como comparador independiente sin auditoría específica |

Los estados anteriores indican factibilidad potencial, no aceptación de datos. La ficha completa se conservará en `validation/sources/`.

## KPI

- **Meta operativa:** MAPE ≤35 %.
- **Estado:** no evaluado.
- **Comparador horario:** pendiente de confirmar una serie de red independiente.
- **Comparador anual/sectorial:** pendiente de auditar el balance oficial.
- **Regla:** si el balance se usa para shares o escalamiento, la comparación contra él se etiqueta como consistencia condicionada.

No se publicará `cumple` hasta que exista una fila en `kpi_validation.csv`, una explicación en `cumplimiento_kpi.md`, una ficha firmada/revisada y un manifiesto reproducible.

## Próximas acciones

1. Registrar la respuesta de Stromnetz Berlin cuando llegue y actualizar el dictamen semántico, temporal y cartográfico.
2. Ejecutar la normalización `Europe/Berlin` → UTC para 2023 y generar la primera serie horaria de entrada.
3. Incorporar la Strombilanz corregida como referencia anual y documentar el escalamiento.
4. Comparar los perfiles HV 2019–2023 una vez resuelto el contrato temporal y registrar cambios de metodología.
5. Conservar la geometría BKG `11000` y documentar CRS, fecha de vigencia y hash en cada corrida.
6. Completar las correspondencias territoriales y el contrato de sectores alemanes.
7. Emitir el dictamen de Fase 0 antes de descargar o transformar grandes volúmenes de datos.

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

## Regla de actualización

Cada modificación futura debe añadir una fila a la bitácora y actualizar la tabla de fases. La entrada debe indicar qué evidencia nueva se generó, qué decisión se tomó, qué limitación permanece y cuál es la siguiente acción. No se deben borrar estados anteriores ni reemplazar resultados desfavorables por versiones favorables.
