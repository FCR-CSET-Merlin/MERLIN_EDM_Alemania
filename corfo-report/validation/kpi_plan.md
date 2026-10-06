# Plan de evidencia KPI — Berlín, Alemania

**Estado:** `expansión multianual consolidada; versión reportable vigente d=8`. Se completaron la validación 2023, el holdout temporal 2024 y los controles anual/espacial de la expansión con su clasificación de dependencia. La corrida d=3 exclusivamente 2023 queda como línea base histórica.

El contrato operativo completo está en
[`contrato_validacion_berlin.md`](sources/contrato_validacion_berlin.md). Este
archivo fija la relación entre las capas de evidencia y el umbral comprometido.

La identificación formal de la versión vigente está en [`berlin/modelo_vigente.md`](berlin/modelo_vigente.md).

## Meta

Meta operativa: **MAPE menor o igual a 35 %**. El criterio contractual se copiará literalmente desde la matriz CORFO vigente; si exige `<35 %`, se reportarán ambos criterios sin modificar los datos.

## Indicadores y comparadores

| Capa | Indicador | Referencia | Uso en KPI | Estado |
|---|---|---|---|---|
| A | MAPE, MAE, RMSE, sesgo y error de punta horarios | Perfil HV reservado temporalmente | KPI operativo interno | Vigente d=8: validación 2023 y holdout 2024 cumplen; d=3 queda histórico |
| B | Energía anual, sesgo energético y shares sectoriales | Strombilanz Berlin | Consistencia externa condicionada | Ejecutado: modelo 2023 vs balance −0,357941 % |
| C | Correlación, MAE/RMSE de shares y cobertura distrital | Umweltatlas Berlin | Consistencia espacial externa | Ejecutado como asignación condicionada; KPI espacial independiente no evaluable |
| D | Correlación y error de perfil normalizado | SMARD/ENTSO-E | Contexto horario | No válido para MAPE Berlín |
| E | MAPE, MAE, RMSE, sesgo y punta horarios | Serie independiente de Berlín | Validación horaria externa | No evaluable; no se identificó una fuente pública compatible |

La capa A no debe presentarse como validación independiente. Las capas B y C no deben convertirse artificialmente en MAPE horario porque miden consumo final anual y distribución espacial. La capa D solo controla forma agregada, dado que su perímetro no coincide con Berlín.

No se excluyen años, sectores o distritos por conveniencia. `no_evaluable` se usa para faltantes, referencia cero o perímetro incompatible; nunca se convierte en un MAPE favorable.

## Registro mínimo por fila

```text
id_evidencia, compromiso, indicador, pais, territorio, nivel, año,
sector, n_observaciones, n_validas, mape_pct, mae, rmse,
umbral_pct, criterio, cumple_umbral, comparador,
comparador_independiente, dependencia_input, fuente_referencia,
hash_entrada, hash_salida, estado_evidencia, notas
```

## Artefactos obligatorios

1. `validation/kpi_validation.csv` — una fila por combinación evaluada.
2. `results/tables/kpi_summary.csv` — denominador y estado general.
3. `validation/cumplimiento_kpi.md` — fórmula, resultados sin redondear y limitaciones.
4. `validation/ficha_evidencia_berlin.md` — fuente, método, versión, responsable y aceptación.
5. `validation/manifiesto_berlin.json` — entradas, salidas, hashes, commit y entorno.
6. `validation/berlin/comparaciones_externas_2023.csv` — plantilla de resultados externos.
7. `validation/sources/comparaciones_externas_berlin.csv` — matriz de fuentes y dependencias.

La existencia de estos archivos demuestra trazabilidad del cálculo, no el cumplimiento automático del KPI.
