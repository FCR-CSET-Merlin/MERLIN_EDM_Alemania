# Auditoría de matriz proxy distrito–sector de Berlín 2023

Estado: **matriz construida y reconciliada; validación sectorial independiente pendiente**.

## Regla aplicada

Los pesos espaciales provienen de `j2023g` del Umweltatlas. `Haushalt`, `Nachtspeicher` y `Wärmepumpe` se usan como proxy residencial; `Gewerbe` como proxy comercial; `Lastgangkunde` se reparte entre industria, comercio y transporte con la proporción agregada de Strombilanz. La matriz se reconcilia por IPF a los totales sectoriales de Strombilanz y a los totales distritales normalizados al mismo total.

- Distritos: **12**.
- Total distrital `j2023g`: **11899.370000 GWh**.
- Total de detalle Umweltatlas: **11758.050000 GWh**.
- Diferencia detalle frente a `j2023g`: **-1.187626 %**.
- Total objetivo Strombilanz: **11780.229000 GWh**.
- Residuo máximo por distrito después de IPF: **1.027729013e-10 GWh**.
- Residuo máximo por sector después de IPF: **2.27373675443e-13 GWh**.
- Suma de shares por distrito: **1.000000000000–1.000000000000**.

## Limitaciones

`Lastgangkunde` no identifica por sí solo industria, comercio ni transporte; su partición es un prior. La categoría pública no es separable en la Strombilanz utilizada y queda con objetivo cero. La matriz es anual: para generar shares mensuales se requiere un perfil temporal sectorial normalizado. Esta salida sirve como insumo de desagregación y no como KPI espacial o sectorial independiente.
