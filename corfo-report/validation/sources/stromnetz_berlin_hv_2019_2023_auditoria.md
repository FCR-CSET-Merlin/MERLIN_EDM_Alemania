# Auditoría de perfiles HV 2019–2023 y semántica de la carga

**Fecha de acceso:** 21 de septiembre de 2026  
**Fuente:** [Stromnetz Berlin — publicación EnWG](https://www.stromnetz.berlin/uber-uns/veroffentlichungspflichten/energiewirtschaftsgesetz-enwg/)  
**Serie auditada:** `Jahreshöchstlast der Netzlast – Lastverlauf Hochspannung`  
**Uso previsto:** objetivo horario candidato para `Berlin-administrative` (`11000`), identificado como proxy

## Qué está confirmado por la documentación oficial

Stromnetz Berlin define `Last` como la potencia o energía que todos los consumidores toman actualmente a través de la red. Define `Lastgang` como el conjunto de promedios de potencia medidos en periodos de 15 minutos; cuatro valores de 15 minutos representan el consumo de una hora. Véase el [glosario oficial](https://www.stromnetz.berlin/glossar/).

La página EnWG publica los archivos bajo la categoría `Jahreshöchstlast der Netzlast` y define la `Jahreshöchstlast` como el mayor valor de potencia ocurrido en el año considerando todas las tensiones. Eso no significa que cada archivo por nivel sea la carga total del sistema: el archivo HV es el perfil de la categoría **alta tensión**.

La tabla de `Jahresarbeit je Netz- und Umspannebene` indica además que las cifras por nivel incluyen la entrega a la red o nivel de transformación aguas abajo. Por esa razón, el perfil HV es una medida de carga de red en alta tensión que incorpora transferencia hacia niveles inferiores; no es consumo final y no se puede sumar con MV, MV/LV o LV.

El operador publica por separado las pérdidas, la `Restlast` SLP y los programas pronosticados. La `Restlast` se calcula como `Netzlast − Netzverluste − Entnahmelast leistungsgemessener Kunden`; por tanto, no es la misma magnitud que el perfil HV.

## Controles de los archivos originales

La energía se calculó como `sum(Wert_kW × 0,25 h)`. Los puntos se conservaron en el orden original; no se eliminaron duplicados ni se interpolaron fechas.

| Año | Registros válidos | Esperados | Primera marca | Última marca | Etiquetas locales duplicadas | Saltos distintos de 15 min | Máximo declarado coincide | Energía declarada |
|---:|---:|---:|---|---|---:|---:|---|---:|
| 2019 | 35.040 | 35.040 | 01.01.2019 00:15 | 01.01.2020 00:00 | 4 | 2 | Sí | 13.275.601.333 kWh |
| 2020 | 35.136 | 35.136 | 01.01.2020 00:15 | 01.01.2021 00:00 | 16 | 8 | Sí | 12.247.204.540 kWh |
| 2021 | 35.040 | 35.040 | 01.01.2021 00:15 | 01.01.2022 00:00 | 8 | 14 | Sí | 12.271.750.956 kWh |
| 2022 | 35.040 | 35.040 | 01.01.2022 00:15 | **01.01.2022 00:00** | 8 | 5 | Sí | 12.142.364.343 kWh |
| 2023 | 35.040 | 35.040 | 01.01.2023 00:15 | 01.01.2024 00:00 | 4 | 2 | Sí | 11.812.177.946 kWh |

El encabezado de cada archivo declara los siguientes máximos: 2.268.885 kW (2019), 2.058.988 kW (2020), 2.061.086 kW (2021), 2.050.740 kW (2022) y 2.022.067 kW (2023). Todos coinciden con el máximo recalculado desde `Wert`.

El desfase de 18 kWh observado en 2019 entre la suma de los valores enteros y el campo `Arbeit` es un efecto de redondeo de los valores publicados. En 2020 el CSV redondea a kWh entero; el histórico XLSX conserva `12.247.204.539,75 kWh`. En 2021–2023 las sumas coinciden con el encabezado publicado.

## Control de timestamps y DST

Las etiquetas deben interpretarse como marcas locales de `Europe/Berlin` asociadas a intervalos de 15 minutos, pero la documentación pública no indica si `Datum/Zeit` representa inicio o fin del intervalo ni cómo codifica el `fold` de la hora repetida.

Los saltos de 75 minutos en primavera y de −45 minutos en otoño son compatibles con la forma en que el proveedor etiqueta los intervalos alrededor del cambio horario, pero no permiten reconstruir por sí solos un timestamp UTC inequívoco. Además, hay anomalías específicas que requieren aclaración:

- En 2020 el CSV presenta bloques fuera de orden alrededor del 29–30 de marzo y 25–26 de octubre. Sus valores coinciden con el histórico XLSX, pero las etiquetas temporales no son equivalentes en 20.164 de las 35.136 filas comparadas.
- En 2021 aparecen retrocesos y saltos de fecha adicionales alrededor del 25–26 de octubre, además de la repetición de la hora de otoño.
- En 2022 la última marca del CSV es `01.01.2022 00:00`; el histórico XLSX la registra como `01.01.2023 00:00`.
- En 2019 y 2023 también existen etiquetas repetidas en la transición de otoño; no deben deduplicarse sin conservar el orden y la información de cambio horario.

**Decisión de integración:** conservar los archivos originales y sus timestamps tal como fueron publicados; antes de entrenar con más de un año, generar una columna UTC reproducible usando `Europe/Berlin`, el orden de las filas y una regla explícita para el intervalo final. No se autoriza una corrección manual de fechas ni la eliminación de duplicados sin respuesta del operador.

Para el piloto se mantiene 2023 como año inicial de reconstrucción, porque su cobertura energética y su estructura son consistentes y la anomalía temporal queda localizada en la transición DST. La extensión 2019–2022 queda condicionada a la normalización temporal documentada.

## Hashes y enlaces

| Año | URL original | SHA-256 |
|---:|---|---|
| 2019 | [Jahreshoechstlast-2019.csv](https://www.stromnetz.berlin/files/globalassets/dokumente/veroffentlichungspflichten/2019/jahreshoechstlast-2019.csv) | `70dc6d21c2b468ac5d9d02aa5b2a774e2c311a1d9362ff1fbcc14631a7b7868e` |
| 2020 | [Jahreshoechstlast-2020-Hochspannung.csv](https://www.stromnetz.berlin/files/globalassets/dokumente/veroffentlichungspflichten/2020/jahreshoechstlast-2020-hochspannung.csv) | `457c4fd1f5f2177387db0d641b77d82cdfbe3cf12f6ccf5d4fdef7886fe83ea9` |
| 2021 | [jahreshoechstlast-2021-hochspannung.csv](https://www.stromnetz.berlin/files/globalassets/dokumente/veroffentlichungspflichten/2021/jahreshoechstlast-2021-hochspannung.csv) | `a0bcfb1910dac6db8e75701e0fc763e4f484153ade3f95fa8030cea23f1f5e88` |
| 2022 | [Jahreshoechstlast-2022-Hochspannung.csv](https://www.stromnetz.berlin/files/globalassets/dokumente/veroffentlichungspflichten/2022/Jahreshoechstlast-2022-Hochspannung.csv) | `688f5d58fd80f581a002412ba3f5fade9c4b0effada591cc56ef7188758f27fa` |
| 2023 | [Jahreshoechstlast-2023-Hochspannung.csv](https://www.stromnetz.berlin/files/globalassets/dokumente/veroffentlichungspflichten/2023/Jahreshoechstlast-2023-Hochspannung.csv) | `8ce40b404dfaafbe55051db1926e204712205d64cbeac0a5bef95c5faa76a6c3` |
| Histórico XLSX HV 2020–2025 | [historie-jahreshoechstlast-hochspannung-berlin.xlsx](https://www.stromnetz.berlin/files/globalassets/dokumente/opendata/veroffentlichungspflichten/historie-jahreshoechstlast-hochspannung-berlin.xlsx) | `2bb8bcc877d4afee10133ae9b936342706cecab89bba381348ac09b33a737281` |

## Dictamen semántico

**GO condicionado para el objetivo horario de red:** la documentación confirma que la serie representa un `Lastgang` de red en alta tensión, en kW medios por 15 minutos, con energía anual declarada y transferencia a niveles aguas abajo incluida.

**Pendiente de confirmación del operador:** alcance exacto de clientes y transferencias incluidos en HV, tratamiento de generación/flujo inverso, definición de `Datum/Zeit` y perímetro cartográfico asociado al perfil.
