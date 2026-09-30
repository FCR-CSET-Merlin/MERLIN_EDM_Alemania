# Auditoría de desagregación distrito–sector de Berlín 2023

Estado: **controles de conservación aprobados; resultado espacial y sectorial condicionado**.

## Regla aplicada

Para cada hora completa se aplica `L_d,h,s = L_Berlín,h × district_weight_d × sector_share_d,s`. Los pesos distritales y shares sectoriales son anuales y se difunden a todas las horas (`annual_broadcast`).

- Filas de inferencia utilizadas: **8,740/8,760 (99.771689 %)**.
- Filas horarias distrito–sector: **524,400**.
- Filas anuales distrito–sector: **60**.
- Energía Berlín predicha en filas completas: **11738.062670 GWh**.
- Residuo máximo horario ciudad vs. distritos: **6.8212102633e-13 MW**.
- Residuo máximo horario distrito vs. sectores: **3.81154677598e-07 MW**.
- Residuo máximo anual distrito: **2.27268901654e-06 GWh**.
- Hora de instantánea cartográfica: **2023-11-30T17:00:00+00:00** (2023-11-30T18:00:00+01:00), máxima carga predicha de Berlín.

## Evidencia generada

- Tabla horaria larga: `corfo-report/results/tables/berlin_district_sector_d3_2023_hourly.csv.gz`.
- Tabla anual larga: `corfo-report/results/tables/berlin_district_sector_d3_2023_annual.csv`.
- Tabla anual ancha: `corfo-report/results/tables/berlin_district_sector_d3_2023_annual_wide.csv`.
- Resumen horario por sector: `corfo-report/results/tables/berlin_district_sector_d3_2023_hourly_sector_summary.csv.gz`.
- Mapas anuales y de la instantánea horaria: ver el manifiesto de figuras y los archivos PNG/SVG en `corfo-report/results/figures/`.

## Limitaciones que deben acompañar cualquier uso

La salida conserva exactamente la energía agregada del modelo por construcción, pero no demuestra que la red haya aprendido diferencias horarias entre distritos o sectores. Los shares anuales provienen de proxies de Umweltatlas/Strombilanz; el sector público queda con share estructural cero; la cobertura no incluye 20 horas faltantes; y el alcance HV frente al perímetro administrativo `11000` aún requiere confirmación de Stromnetz Berlin. Por ello, estas tablas y mapas se reportan como escenario de desagregación reproducible, no como validación externa independiente.
