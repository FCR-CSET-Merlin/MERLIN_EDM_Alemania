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
| Fase 0 — Factibilidad y contrato de datos | **En curso** | Restlast SLP 2023 auditada: 35.040 intervalos de 15 min, pero no representa demanda total; perímetro y categorías restantes pendientes | [Auditoría SLP 2023](sources/stromnetz_berlin_restlast_2023.md), [inventario](sources/inventario_fuentes.csv) | Fuentes fichadas, hashes registrados, perímetro y cobertura verificados, dictamen GO/GO condicionado/NO-GO |
| Fase 1 — Homologación territorial, sectorial y temporal | Pendiente | Sin contrato alemán validado | — | Correspondencias de red, Berlín, distritos y sectores; unidades y DST verificadas |
| Fase 2 — Línea base y adaptación | Pendiente | No hay ejecución del modelo alemán | — | Modelo, columnas, scaler, entorno y diferencias Chile–Alemania identificados |
| Fase 3 — Reconstrucción histórica de Berlín | Pendiente | No hay series ni tablas alemanas generadas | [Series](../results/timeseries/README.md) | Corrida reproducible con cobertura, perímetro y hashes |
| Fase 4 — Validación y KPI | Pendiente | KPI alemán no evaluado | [Plan KPI](kpi_plan.md), [cumplimiento](cumplimiento_kpi.md) | CSV KPI, resumen, ficha y manifiesto revisados |
| Fase 5 — Escalamiento territorial | Pendiente | No iniciada | — | Piloto Berlín cerrado y reproducible |

## Estado de fuentes

| Grupo | Estado | Decisión actual |
|---|---|---|
| Stromnetz Berlin Restlast SLP 2023 | **En revisión / GO condicionado** | Serie completa de 35.040 intervalos; es carga residual SLP calculada, no demanda total; falta perímetro y DST |
| Statistik Berlin-Brandenburg | Candidata anual | Revisar balance, sectores, unidades y revisiones |
| Umweltatlas Berlin | Candidata espacial | Revisar cobertura distrital, privacidad y año de referencia |
| DWD/ERA5-Land | Candidata climática | Seleccionar fuente, versión y tratamiento horario |
| VG250/Zensus/Destatis/BA | Covariables y límites | Incorporar solo después de fijar el contrato territorial |
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

1. Auditar otras categorías publicadas por Stromnetz Berlin y determinar si existe una serie anual de demanda total.
2. Resolver el perímetro y la desambiguación DST del archivo Restlast SLP 2023.
3. Obtener y fichar el balance eléctrico de Berlín y su clasificación sectorial.
3. Fijar el período común y la definición formal del objetivo (`Berlin-administrative` o `Stromnetz-Berlin-area`).
4. Completar las correspondencias territoriales y el contrato de sectores alemanes.
5. Emitir el dictamen de Fase 0 antes de descargar o transformar grandes volúmenes de datos.

## Bitácora

| Fecha | Fase | Acción / decisión | Resultado | Evidencia |
|---|---|---|---|---|
| 2026-09-21 | Preparación | Se creó la reportabilidad alemana, se separó la referencia chilena y se publicó el plan de adaptación | Commit `c951f09`; estructura lista | [Reportabilidad](../README.md), [plan](../../PLAN_TRABAJO_ADAPTACION_ALEMANIA.md) |
| 2026-09-21 | Fase 0 | Se inicializó este registro de avance | Fase 0 marcada como `En curso`; no se declara KPI | Este archivo |
| 2026-09-21 | Fase 0 | Se descargó y auditó Restlast SLP 2023 | 35.040 intervalos completos; GO condicionado para SLP, no demanda total | [Auditoría SLP](sources/stromnetz_berlin_restlast_2023.md) |

## Regla de actualización

Cada modificación futura debe añadir una fila a la bitácora y actualizar la tabla de fases. La entrada debe indicar qué evidencia nueva se generó, qué decisión se tomó, qué limitación permanece y cuál es la siguiente acción. No se deben borrar estados anteriores ni reemplazar resultados desfavorables por versiones favorables.
