# Cumplimiento KPI — Berlín, Alemania

**Estado:** Fase 4 cerrada con limitación documentada. El KPI horario interno 2023 y el holdout temporal 2024 cumplen el umbral operativo; no existe una fuente horaria pública independiente con perímetro Berlín compatible.

## Resultados horarios

| Evaluación | n válidas | Cobertura | MAPE | MAE | RMSE | Estado |
|---|---:|---:|---:|---:|---:|---|
| Test interno HV 2023, d=3 | 1.311 | 100,000000 % de la partición test | 5,089161454 % | 70,395301 MW | 86,549150 MW | **Cumple internamente** |
| Holdout temporal HV 2024, d=3 congelado | 8.776 | 99,908925 % | 3,095865639 % | 41,850056 MW | 57,472507 MW | **Cumple temporalmente; mismo operador** |

El holdout 2024 conserva arquitectura, variables, scaler y shares 2023. Las ocho horas sin features d=3 completas no fueron imputadas. El resultado mide generalización temporal dentro de Stromnetz Berlin y no constituye validación independiente de fuente.

## Controles anual y espacial

La inferencia 2023 en filas completas suma 11.738,062673 GWh frente a 11.780,229000 GWh de la Strombilanz (−0,357941 %). Se clasifica como **consistencia condicionada** porque el balance aportó shares sectoriales al contrato y la cobertura fue 8.740/8.760 horas. La evidencia está en [`berlin/annual_2023_model_control.md`](berlin/annual_2023_model_control.md).

La desagregación a 12 Bezirke reproduce los shares `j2023g` por construcción. La capa espacial queda **no evaluable como KPI independiente**; el detalle está en [`berlin/inference_2023/spatial_validation_berlin_d3_2023.md`](berlin/inference_2023/spatial_validation_berlin_d3_2023.md).

## Limitación de validación externa

La revisión de fuentes no encontró una curva horaria pública medida por una entidad independiente con perímetro exactamente coincidente con Berlin-administrative (11000). SMARD, ENTSO-E y 50Hertz se mantienen como contexto regional, no como verdad de terreno berlinesa.
