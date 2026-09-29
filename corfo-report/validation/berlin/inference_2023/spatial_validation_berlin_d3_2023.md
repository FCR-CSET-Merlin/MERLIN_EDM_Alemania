# Capa espacial Berlín 2023 — inferencia d=3

## Regla provisional de desagregación

Para cada hora completa de la inferencia agregada se calcula `P_d,h = P_Berlin,h × w_d`, donde `w_d = j2023g_d / Σj2023g_d` y `j2023g` es el consumo anual 2023 por distrito publicado por Umweltatlas. La regla mantiene la forma horaria del agregado y asigna a cada distrito una participación anual fija.

- Distritos cubiertos: **12/12**.
- Total de referencia `j2023g`: **11899.370000 GWh**.
- Energía predicha Berlín en las filas completas: **11738.062673 GWh**.
- Diferencia del total predicho frente a Umweltatlas: **-1.355596 %**.
- Error máximo de participación distrital: **0.000000000000 puntos porcentuales**, por construcción.

## Evaluación de la capa espacial

El resultado distrital es **consistencia condicionada; no validación espacial independiente**. Las mismas participaciones `j2023g` de Umweltatlas que se usan como pesos definen la referencia de shares, por lo que una coincidencia de participaciones no demuestra que la red haya aprendido diferencias horarias entre distritos. La única discrepancia independiente disponible en esta etapa es el control del total agregado, afectado además por la cobertura de 8.740/8.760 horas y por la diferencia de perímetro entre HV y consumo distrital.

Para declarar un KPI espacial independiente se requiere una serie horaria distrital externa o variables explicativas territorializadas (por ejemplo, cargas medidas por distrito, perfiles de clientes o un procedimiento de calibración con observaciones fuera de `j2023g`). Hasta entonces, esta regla sirve para producir un escenario distrital reproducible y para preparar la integración cartográfica.
