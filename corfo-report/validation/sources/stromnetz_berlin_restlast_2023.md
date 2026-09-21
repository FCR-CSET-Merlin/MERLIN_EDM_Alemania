# Auditoría de fuente — Stromnetz Berlin Restlast SLP 2023

**Estado:** `en revisión`; no aceptada todavía como demanda total de red ni como comparador KPI independiente.
**Fecha de acceso:** 21 de septiembre de 2026.
**Rol previsto:** candidato para perfil horario de clientes SLP y control de cobertura.

## Procedencia

- Página oficial de obligaciones EnWG: <https://www.stromnetz.berlin/uber-uns/veroffentlichungspflichten/energiewirtschaftsgesetz-enwg/>
- Archivo descargado: <https://www.stromnetz.berlin/files/globalassets/dokumente/veroffentlichungspflichten/2023/Summenlast-nicht-leistungsgemessene-Kunden-SLP-2023.csv>
- Archivo temporal auditado: `/tmp/stromnetz_berlin_restlast_2023.csv`
- SHA-256: `db5be7b232e5a2a423c267babf425920f4c62293b91aeefe195b526ddb8544`
- Formato: CSV separado por `;`, encabezado en alemán, valores numéricos con punto como separador de miles.

## Definición de la variable

La página de Stromnetz Berlin define la `Summenlast der nicht leistungsgemessenen Kunden (Restlast)` como la carga agregada de clientes con perfiles estándar (`SLP-Kunden`). La fuente indica que se obtiene por cálculo y que:

`Restlast = Netzlast - Netzverluste - Entnahmelast leistungsgemessener Kunden`.

Por lo tanto, la serie no debe denominarse demanda total de Berlín. Es una carga residual de clientes no medidos con registro de potencia y excluye explícitamente la carga de clientes con medición registrada y las pérdidas de red mediante la definición anterior.

## Controles realizados

| Control | Resultado |
|---|---|
| Año declarado en el archivo | 2023 |
| Filas de datos | 35.040 |
| Resolución | 15 minutos; columna `kW` |
| Primer intervalo | 01.01.2023 00:15 |
| Último intervalo | 01.01.2024 00:00 |
| Cobertura esperada | 365 × 96 = 35.040 intervalos |
| Mínimo/máximo | 295.313 / 1.054.534 kW |
| Energía sumada | 5.463.273.992 kWh, usando 0,25 h por intervalo |
| Energía declarada en el archivo | 5.463.273.992 kWh |
| Faltantes numéricos | No observados en las 35.040 filas |
| Timestamps locales únicos | 35.036; hay duplicaciones durante el cambio horario de otoño |

La energía calculada desde los intervalos coincide con la energía declarada por la fuente. Los timestamps están expresados como hora local sin un identificador de zona: el 29 de octubre se repiten los intervalos 02:15, 02:30, 02:45 y 03:00; el 26 de marzo falta el bloque local equivalente al cambio de primavera. Antes de convertir a horas se debe conservar una representación consciente de `Europe/Berlin` y una regla de desambiguación.

## Perímetro y uso metodológico

La página identifica la variable como perteneciente al `Berliner Verteilungsnetz`, pero todavía falta demostrar que el área de red coincide exactamente con el límite administrativo de Berlín. La fuente debe cruzarse con los límites VG250 y con los metadatos del área servida antes de etiquetar la salida como `Berlin-administrative`.

**Decisión provisional:**

- `GO condicionado` para usar el archivo como insumo o referencia del perfil horario SLP, una vez resueltos zona horaria y perímetro.
- `NO` como sustituto de la demanda total de red hasta incorporar carga de clientes medidos, pérdidas y el perímetro completo.
- `NO` como validación independiente si el mismo archivo o sus componentes participan en el escalamiento del modelo.

## Acciones pendientes

1. Auditar al menos un archivo adicional de `Netzlast` o de las categorías de carga publicadas para establecer si existe una serie horaria total.
2. Comparar el perímetro de Stromnetz Berlin con Berlín administrativo y documentar el código territorial.
3. Descargar versiones históricas de 2019–2023 y repetir los controles de filas, energía, faltantes y DST.
4. Definir si el piloto modelará demanda total de red, Restlast SLP o ambas magnitudes como salidas separadas.
5. Conservar el archivo original o su ubicación externa junto con este hash para la futura corrida reproducible.
