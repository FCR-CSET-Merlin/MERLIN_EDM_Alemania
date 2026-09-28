# Tabla integrada HV–temperatura — Berlín 2023

**Estado:** insumo preparado para la adaptación; aún no es una entrada completa de la red neuronal.  
**Demanda:** Stromnetz Berlin HV 2023, usada como `Stromnetz-Berlin-HV-area-proxy`.  
**Temperatura:** DWD Berlin-Tempelhof, estación `00433`.

## Contrato de unión

La llave es el final de hora UTC:

```text
HV.timestamp_hour_end_utc = DWD.timestamp_utc
```

Se generan ocho columnas climáticas causales:

```text
temperature_t_minus_0_C ... temperature_t_minus_7_C
```

La temperatura se expresa en °C y la demanda conserva `load_mean_MW` y `energy_MWh`. También se incluyen hora, día de semana, mes, día del año y fin de semana en `Europe/Berlin`.

## Controles

| Control | Resultado |
|---|---:|
| Filas HV | 8.760 |
| Filas DWD | 8.760 |
| Filas integradas | 8.760 |
| Filas con ocho temperaturas válidas | 8.740 |
| Filas incompletas | 20 |
| Imputación | No realizada |
| Primer final de hora UTC | `2023-01-01T00:00:00+00:00` |
| Último final de hora UTC | `2023-12-31T23:00:00+00:00` |
| Salida | `prototipo_3/data/de_alemania/berlin_features_2023/berlin_hv_temperature_features_2023.csv` |
| SHA-256 salida | `109ff4f4d6484adba73a5712a792c9e3713053559d6f2dff79c562c815e1c36a` |

Las 20 filas incompletas provienen de los siete rezagos iniciales y de la propagación de los cinco faltantes DWD del 3 de abril. No se descartan del archivo: se marcan con `temperature_complete_8lags=0`.

## Limitaciones antes del entrenamiento

- Faltan shares sectoriales alemanes y la definición de su correspondencia con las entradas chilenas.
- Aún no se ha decidido el calendario de feriados alemán que acompañará las variables cíclicas.
- La semántica exacta del timestamp HV continúa pendiente de Stromnetz Berlin.
- La serie HV y la estación DWD no prueban por sí solas una demanda comunal espacialmente desagregada.
