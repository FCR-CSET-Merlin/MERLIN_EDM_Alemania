# Reproducibilidad de inferencia Berlín d=3 — 2023

Estado: **pass**. Se comparó la inferencia regenerada con el artefacto versionado en el commit `cb1d080`.

- Tolerancia numérica por métrica: **1e-05**.
- MAPE test anterior: **5.089161454 %**.
- MAPE test regenerado: **5.089161564 %**.
- Diferencia: **1.100e-07 puntos porcentuales**.
- Máxima diferencia absoluta entre métricas: **2.706e-06**.

La diferencia queda dentro de la tolerancia y no cambia la conclusión KPI: el MAPE test es aproximadamente 5,089 % y permanece por debajo del umbral operativo de 35 %. Las pequeñas variaciones se atribuyen a la ejecución numérica del mismo modelo y contrato.
