# Auditoría de shares sectoriales del contrato Berlín 2023

Estado: **pass**. Resolución temporal: **`annual_broadcast`**.

Se leyeron los contratos Parquet de `d=3`, `d=5` y `d=8`, en sus particiones de entrenamiento, validación y prueba. Cada columna territorial/sectorial debe contener un único valor durante todas las filas y coincidir con la fila anual oficial.

- Combinaciones auditadas: **54**.
- Shares constantes en todas las filas: **True**.
- Coincidencia con la fuente anual: **True**.
- Error máximo de suma de shares: **0.000e+00**.

La auditoría confirma que no se introdujeron shares mensuales en el contrato regional de Berlín.
