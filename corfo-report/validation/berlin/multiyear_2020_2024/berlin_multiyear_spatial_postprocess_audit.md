# Postproceso espacial y sectorial — expansión multianual Berlín d=8

Se generaron mapas anuales por distrito y por distrito-sector para 2020–2024 a partir de la inferencia agregada seleccionada d=8.

## Reglas

- Distrito: `demanda_distrito_y = demanda_Berlín_y × district_weight_2023`.
- Sector: `demanda_distrito_sector_y = demanda_distrito_y × share_sector_y`.
- Los pesos distritales corresponden al proxy `j2023g` del Umweltatlas 2023 y se mantienen fijos por falta de una serie distrital anual compatible.
- Los shares sectoriales provienen de Strombilanz y son anuales; 2024 usa carry-forward 2023 etiquetado.

## Controles por año

| Año | Horas completas | Energía observada (GWh) | Energía predicha (GWh) | Error predicho-observado (%) | Residuo distrito (GWh) | Residuo distrito-sector (GWh) | Share status |
|---:|---:|---:|---:|---:|---:|---:|---|
| 2020 | 8784 | 12247.204540 | 12120.564860 | -1.034029 | 1.819e-12 | -1.212e-08 | observed_annual |
| 2021 | 8760 | 12271.750956 | 12157.448136 | -0.931430 | 0.000e+00 | 1.819e-12 | observed_annual |
| 2022 | 8613 | 11933.112821 | 11892.011635 | -0.344430 | 0.000e+00 | 1.819e-12 | observed_annual |
| 2023 | 8747 | 11791.156626 | 12074.477890 | 2.402828 | 0.000e+00 | -1.819e-12 | observed_annual |
| 2024 | 8773 | 11817.218542 | 12095.962062 | 2.358791 | 0.000e+00 | -1.819e-12 | frozen_last_available_for_holdout_only |

Residuos máximos de conservación: **1.819e-12 GWh** a nivel distrito y **1.212e-08 GWh** a nivel distrito-sector.

## Interpretación y limitaciones

La conservación confirma que el postproceso reparte exactamente el agregado predicho. No demuestra que la red haya aprendido diferencias horarias entre distritos: el peso espacial es externo y fijo. La comparación espacial/sectorial debe presentarse como escenario condicionado hasta disponer de mediciones distritales independientes.

Figuras: `corfo-report/results/figures/berlin_demanda_distrital_multiyear_d8_2020_2024.png` y `corfo-report/results/figures/berlin_demanda_distrito_sector_anual_multiyear_d8_2020_2024.png`.
