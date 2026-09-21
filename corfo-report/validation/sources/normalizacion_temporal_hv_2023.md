# Especificación de normalización temporal — HV 2023

**Estado:** especificación validada sobre el archivo original; aún no se ha ejecutado el modelo.  
**Fuente:** `Jahreshoechstlast-2023-Hochspannung.csv`  
**Zona:** `Europe/Berlin`  
**Objetivo:** generar un índice UTC reproducible sin borrar ni sobrescribir las marcas originales.

## Regla

1. Conservar `Datum`, `Zeit`, `Wert` y el número de fila original.
2. Interpretar el primer registro `01.01.2023 00:15` como `2023-01-01 00:15 Europe/Berlin`.
3. Convertir ese instante a UTC.
4. Generar los siguientes instantes agregando exactamente 15 minutos en UTC, respetando el orden original de las 35.040 filas.
5. Convertir el índice UTC a `Europe/Berlin` solo para presentación, conservando el indicador de hora repetida (`fold`) cuando corresponda.
6. Mantener la marca publicada en una columna separada y registrar cualquier diferencia entre la fuente y el índice normalizado.

Pseudocódigo:

```python
inicio_utc = localize("2023-01-01 00:15", "Europe/Berlin").astimezone("UTC")
indice_utc = [inicio_utc + i * timedelta(minutes=15) for i in range(35040)]
```

Este procedimiento usa la secuencia de observaciones y evita deduplicar las horas repetidas del cambio CET/CEST.

## Evidencia de la prueba

| Control | Resultado |
|---|---:|
| Registros | 35.040 |
| Primer UTC | `2022-12-31 23:15:00+00:00` |
| Último UTC | `2023-12-31 23:00:00+00:00` |
| Diferencia entre instantes UTC | siempre 15 minutos |
| Instantes UTC únicos | 35.040 |
| Offsets locales observados | UTC+01:00 y UTC+02:00 |
| Marcas publicadas que difieren del índice normalizado | 2 |
| Hash SHA-256 del índice UTC serializado | `b0edbb1c114dd3fa792e9bf23254456990354622d8a877f4250852e2c19a359c` |

Las dos diferencias están en las transiciones de 2023:

| Fila (base 0) | Marca publicada | Marca normalizada |
|---:|---|---|
| 8.071 | `2023-03-26 02:00` | `2023-03-26 03:00+02:00` |
| 28.903 | `2023-10-29 03:00` | `2023-10-29 02:00+01:00` (`fold=1`) |

La marca original se conserva para auditoría; la marca UTC normalizada será la usada para uniones con temperatura, calendario y otras fuentes. La normalización no altera los valores de potencia ni la energía anual.

## Alcance

Esta especificación se acepta para el piloto 2023. No se aplica automáticamente a 2019–2022: esos archivos presentan anomalías adicionales de fecha y deben revisarse después de recibir la respuesta de Stromnetz Berlin.
