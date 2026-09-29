# Cumplimiento KPI — Berlín, Alemania

**Estado:** KPI horario interno cumplido; validación horaria externa y KPI espacial independiente pendientes.

La meta operativa del piloto es MAPE ≤35 %. La evidencia estructurada está en [`berlin/kpi_validation.csv`](berlin/kpi_validation.csv) y el detalle reproducible de la corrida en [`berlin/inference_2023/berlin_d3_inference_2023_summary.md`](berlin/inference_2023/berlin_d3_inference_2023_summary.md).

## KPI horario interno

| Configuración | Partición | n | MAPE | Umbral | Resultado |
|---|---|---:|---:|---:|---|
| MLP Alemania d=3, τ=1 h, 19 features | test cronológico HV 2023 | 1.311 | 5,089161454 % | ≤35 % | **Cumple internamente** |

La métrica se calcula sobre el mismo perfil HV de Stromnetz Berlin utilizado como objetivo del entrenamiento, con partición temporal reservada. Por ello acredita la reconstrucción interna del piloto, pero no es todavía una validación horaria externa independiente.

La inferencia exportó 8.740 de 8.760 horas (99,771689 %). Las 20 horas sin features climáticas completas no fueron imputadas. El test contiene 1.311 observaciones completas.

## Controles anuales y espaciales

La auditoría reproducible de fuentes está en [`berlin/external_2023/auditoria_homologacion_externa_berlin_2023.md`](berlin/external_2023/auditoria_homologacion_externa_berlin_2023.md). La comparación de la inferencia d=3 con la suma distrital `j2023g` entrega 11.738,062673 GWh frente a 11.899,370000 GWh (−1,355596 %), pero es un control condicionado por cobertura y perímetro.

La regla distrital `P_d,h = P_Berlin,h × (j2023g_d / Σj2023g_d)` genera los 12 distritos y reproduce sus shares por construcción. La salida no constituye un KPI espacial independiente; para ello se requiere una referencia horaria distrital o covariables territorializadas no usadas como pesos.
