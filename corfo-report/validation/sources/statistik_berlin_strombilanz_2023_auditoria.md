# Auditoría de referencia anual — Strombilanz Berlin 2023

**Fecha de acceso:** 21 de septiembre de 2026  
**Fuente:** [Amt für Statistik Berlin-Brandenburg — Energie- und CO₂-Bilanz](https://www.statistik-berlin-brandenburg.de/e-iv-4-j/)  
**Informe:** `SB E04-04-00_2023j01_BE.pdf`, 2.ª edición corregida, 25.11.2025  
**SHA-256 del PDF:** `c8617c558fbd7e4bd46954f3487e71ada9302c5a55fbdfae5b3f36bfb5471166`

## Qué mide

La `Strombilanz` es una referencia anual de consumo y flujos eléctricos para Berlín. El informe se basa en la metodología del [Länderarbeitskreis Energiebilanzen](https://www.lak-energiebilanzen.de/) y separa generación interna, compras de electricidad, pérdidas de transmisión, consumo en transformación y consumo final.

El informe define el consumo final como el uso de energía por grupos consumidores. Para 2023, la tabla sectorial usa cuatro categorías compatibles con el piloto:

- industria y minería (`Gewinnung von Steinen und Erden, sonstiger Bergbau und Verarbeitendes Gewerbe`);
- transporte;
- hogares;
- comercio, servicios y otros consumidores (`Gewerbe, Handel und Dienstleistungen und übrige Verbraucher`).

No es una medición horaria ni una serie de retiros de un operador. Por eso se utilizará como referencia anual/sectorial independiente del modelo, manteniéndola separada de la carga HV.

## Valores publicados

| Magnitud | 2020 | 2021 | 2022 | 2023 |
|---|---:|---:|---:|---:|
| Consumo final total (Mill. kWh) | 12.368 | 12.359 | 12.201 | 11.780 |
| Industria y minería (Mill. kWh) | 1.427 | 1.471 | 1.379 | 1.294 |
| Transporte (Mill. kWh) | 838 | 891 | 873 | 912 |
| Hogares (Mill. kWh) | 4.227 | 4.126 | 4.029 | 3.966 |
| GHD y otros (Mill. kWh) | 5.876 | 5.870 | 5.919 | 5.609 |
| Pérdidas de transmisión (Mill. kWh) | 350 | 384 | 340 | 378 |
| Consumo bruto (Mill. kWh) | 13.139 | 13.230 | 12.957 | 12.559 |

En 2023 la suma de los sectores publicados es 11.781 Mill. kWh; la diferencia de 1 Mill. kWh respecto del total corresponde al redondeo de la tabla.

## Comparación anual con el perfil HV

El perfil HV se calculó desde `Wert × 0,25 h` y se expresa en GWh. La diferencia no se interpreta como error del modelo: refleja que una fuente es carga de red por nivel de tensión y la otra es consumo final estadístico.

| Año | HV Stromnetz (GWh) | Consumo final estadístico (GWh) | HV − EEV (GWh) | Diferencia relativa |
|---:|---:|---:|---:|---:|
| 2020 | 12.247,205 | 12.368 | −120,795 | −0,977 % |
| 2021 | 12.271,751 | 12.359 | −87,249 | −0,706 % |
| 2022 | 12.142,364 | 12.201 | −58,636 | −0,481 % |
| 2023 | 11.812,178 | 11.780 | +32,178 | +0,273 % |

**Dictamen:** existe consistencia anual suficiente para usar la Strombilanz como control de escala y tendencia. No se debe convertir esta comparación en una validación horaria ni afirmar equivalencia exacta entre consumo final, carga HV y perímetro de red.

## Uso en el KPI

- `Strombilanz` será comparador anual total y sectorial.
- Si el modelo utiliza estos valores para escalar shares o niveles, el MAPE anual se etiquetará como **consistencia condicionada**.
- La validación horaria seguirá dependiendo del perfil HV y de su normalización temporal.
- La edición corregida 2023 reemplaza cualquier valor preliminar anterior en la ficha del piloto.
