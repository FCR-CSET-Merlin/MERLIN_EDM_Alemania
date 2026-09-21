# Plan de evidencia KPI — Berlín, Alemania

**Estado:** `planificado`; no se ha ejecutado la reconstrucción ni calculado el KPI alemán.

## Meta

Meta operativa: **MAPE menor o igual a 35 %**. El criterio contractual se copiará literalmente desde la matriz CORFO vigente; si exige `<35 %`, se reportarán ambos criterios sin modificar los datos.

## Indicadores

| Indicador | Definición | Referencia | Condición |
|---|---|---|---|
| MAPE anual total | Media del APE en territorios/años definidos | Balance oficial de Berlín | Si participó en la escala, es consistencia condicionada |
| MAPE anual sectorial | Media del APE por sector y territorio | Balance sectorial | Igual condición de independencia |
| MAPE horario | Media del APE en intervalos válidos | Demanda de red | Referencia separada de los insumos de escala |
| MAE/RMSE | Error absoluto y cuadrático | Demanda de red | Complementan el MAPE |
| Cobertura | Intervalos válidos/esperados | Fuente respectiva | Se informa por año y territorio |

No se excluyen años, sectores o distritos por conveniencia. `no_evaluable` se usa para faltantes, referencia cero o perímetro incompatible; nunca se convierte en un MAPE favorable.

## Registro mínimo por fila

```text
id_evidencia, compromiso, indicador, pais, territorio, nivel, año,
sector, n_observaciones, n_validas, mape_pct, mae, rmse,
umbral_pct, criterio, cumple_umbral, comparador,
comparador_independiente, dependencia_input, fuente_referencia,
hash_entrada, hash_salida
```

## Artefactos obligatorios

1. `validation/kpi_validation.csv` — una fila por combinación evaluada.
2. `results/tables/kpi_summary.csv` — denominador y estado general.
3. `validation/cumplimiento_kpi.md` — fórmula, resultados sin redondear y limitaciones.
4. `validation/ficha_evidencia_berlin.md` — fuente, método, versión, responsable y aceptación.
5. `validation/manifiesto_berlin.json` — entradas, salidas, hashes, commit y entorno.

La existencia de estos archivos demuestra trazabilidad del cálculo, no el cumplimiento automático del KPI.
