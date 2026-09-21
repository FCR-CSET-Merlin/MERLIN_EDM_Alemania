# Auditoría de categorías y perímetro — Stromnetz Berlin 2023

**Estado:** perfiles anuales confirmados; perímetro operativo del piloto fijado como Berlín administrativo/HV-MV proxy; semántica exacta del área de red aún pendiente.
**Fecha de acceso:** 21 de septiembre de 2026.
**Fuente principal:** <https://www.stromnetz.berlin/uber-uns/veroffentlichungspflichten/energiewirtschaftsgesetz-enwg/>

## Qué significa la carga residual SLP

`Restlast SLP` es la carga agregada de clientes con perfiles estándar que no tienen medición registrada de potencia. Stromnetz Berlin la define como:

`Restlast = Netzlast − Netzverluste − Entnahmelast leistungsgemessener Kunden`.

Por eso no representa una fracción aleatoria ni la demanda total: deja fuera la carga de clientes con medición registrada —normalmente clientes grandes o con perfiles especiales— y las pérdidas de red. La serie de pronóstico SLP tampoco es una medición: es la suma de programas de los comercializadores basada en consumos anuales previstos y perfiles asignados.

## Archivos auditados

Todos los archivos tienen 35.040 registros de 15 minutos para 2023, desde `01.01.2023 00:15` hasta `01.01.2024 00:00`. Los cuatro intervalos duplicados del horario de otoño deben conservarse con una zona horaria consciente de `Europe/Berlin`.

| Categoría | Archivo | Energía 2023 | Máximo | Interpretación |
|---|---|---:|---:|---|
| Alta tensión | [Jahreshöchstlast 2023 Hochspannung](https://www.stromnetz.berlin/files/globalassets/dokumente/veroffentlichungspflichten/2023/Jahreshoechstlast-2023-Hochspannung.csv) | 11.812 GWh | 2.022 MW | Candidato principal a perfil agregado del nivel superior de red; requiere confirmar semántica exacta |
| Alta/media tensión | [Hochspannung-Mittelspannung](https://www.stromnetz.berlin/files/globalassets/dokumente/veroffentlichungspflichten/2023/Jahreshoechstlast-2023-Hochspannung-Mittelspannung.csv) | 11.087 GWh | 1.912 MW | Nivel jerárquico inferior; no sumar con alta tensión |
| Media tensión | [Mittelspannung](https://www.stromnetz.berlin/files/globalassets/dokumente/veroffentlichungspflichten/2023/Jahreshoechstlast-2023-Mittelspannung.csv) | 11.225 GWh | 1.933 MW | Nivel jerárquico; no sumar con otros niveles |
| Media/baja tensión | [Mittelspannung-Niederspannung](https://www.stromnetz.berlin/files/globalassets/dokumente/veroffentlichungspflichten/2023/Jahreshoechstlast-2023-Mittelspannung-Niederspannung.csv) | 6.770 GWh | 1.287 MW | Subconjunto jerárquico |
| Baja tensión | [Niederspannung](https://www.stromnetz.berlin/files/globalassets/dokumente/veroffentlichungspflichten/2023/Jahreshoechstlast-2023-Niederspannung.csv) | 6.827 GWh | 1.280 MW | Subconjunto jerárquico |
| Pérdidas | [Summenlast Netzverluste 2023](https://www.stromnetz.berlin/files/globalassets/dokumente/veroffentlichungspflichten/2023/Summenlast-Netzverluste-2023.csv) | 394,9 GWh | 78,8 MW | Pérdidas calculadas; no demanda de consumidores |
| Restlast SLP | [Summenlast nicht leistungsgemessene Kunden 2023](https://www.stromnetz.berlin/files/globalassets/dokumente/veroffentlichungspflichten/2023/Summenlast-nicht-leistungsgemessene-Kunden-SLP-2023.csv) | 5.463 GWh | 1.055 MW | Clientes SLP no medidos; no demanda total |
| Pronóstico SLP | [Fahrplanprognosen SLP 2023](https://www.stromnetz.berlin/files/globalassets/dokumente/veroffentlichungspflichten/2023/Summenlast-Fahrplanprognosen-SLP-2023.csv) | 5.689 GWh | 1.296 MW | Programa pronosticado; no observación independiente |

Los valores de energía se calcularon sumando `kW × 0,25 h` y coinciden con el campo `Arbeit in kWh` de cada archivo. Los niveles de tensión son jerárquicos: la energía y el máximo disminuyen o cambian según el nivel, por lo que no corresponde sumarlos.

## Candidato para la variable horaria

El archivo de alta tensión es el candidato principal para representar una carga agregada del nivel superior de la red porque es anual, horario-subdiario y tiene la mayor cobertura del conjunto publicado. Sin embargo, antes de fijarlo como `demanda total de Berlín` se debe confirmar si el perfil corresponde a la carga total transferida por el nivel de alta tensión o solamente a clientes conectados directamente en ese nivel.

La decisión provisional es:

- **GO condicionado:** usar el perfil de alta tensión como objetivo horario candidato.
- **GO:** conservar Restlast SLP, pérdidas y pronóstico como componentes explicativos o controles separados.
- **NO:** sumar perfiles de tensión entre sí o tratar el pronóstico SLP como medición.
- **Pendiente:** validar semántica, perímetro y relación con consumo final antes de entrenar o calcular KPI.

## Perímetro del área de red

El histórico oficial de área de red (`historie-netzgebietsdaten-berlin.xlsx`) informa para 2023:

- área geográfica del área de red: **891,12 km²**;
- área servida en alta/media tensión: **891,12 km²**;
- área servida en baja tensión: **503,5 km²**;
- población del área de red: **3.782.202** habitantes.

La página vigente de publicación EnWG de Stromnetz Berlin informa, para sus datos actuales, un área geográfica del área de red de **1.046,64 km²**, un área servida en alta/media tensión de **891,12 km²** y un área servida en baja tensión de **525,27 km²**. La ficha general de [cifras y datos](https://www.stromnetz.berlin/uber-uns/zahlen-daten-fakten/) presenta, en cambio, **891,12 km²** como superficie geográfica del área de red. Por tanto, el operador está publicando dos magnitudes que no deben mezclarse sin una aclaración metodológica.

Como referencia, Destatis registra para Berlín (código 11000) una superficie administrativa de **891,12 km²**: <https://genesis.destatis.de/datenbank/online/statistic/11111/table/11111-0002/search/s/MTExMTE%3D>. El Amt für Statistik Berlin-Brandenburg informa 89.112 hectáreas para Berlín en 2023: <https://www.statistik-berlin-brandenburg.de/157-2024/>.

**Dictamen operativo:** el piloto se fija en Berlín administrativo, código `11000`, con geometría oficial BKG VG250 y superficie nominal de 891,12 km². La serie HV se etiqueta `Stromnetz-Berlin-HV-area-proxy`: su área servida HV/MV coincide en superficie con Berlín, pero no se declara identidad geométrica. Los 1.046,64 km² se conservan como métrica regulatoria separada y no se usan para ampliar el polígono, agregar covariables o calcular KPI. La decisión y la evidencia reproducible están en [decisión territorial del piloto](decision_perimetro_berlin.md).

## Acciones pendientes de confirmación semántica

1. Solicitar a Stromnetz Berlin la definición cartográfica de `geografische Fläche des Netzgebietes` y la cobertura exacta de los archivos HV 2019–2023.
2. Conservar y versionar la geometría BKG `ars=11000` en cada corrida, con CRS y fecha de vigencia documentados.
3. Repetir los controles de energía, cobertura y DST para HV 2019–2023 y registrar cualquier cambio de perímetro.
4. Revisar si los balances anuales y los datos espaciales de Berlín utilizan el mismo territorio administrativo antes de usarlos para escalar o validar.

## Hashes de los archivos descargados

| Archivo | SHA-256 |
|---|---|
| Hochspannung 2023 | `8ce40b404dfaafbe55051db1926e204712205d64cbeac0a5bef95c5faa76a6c3` |
| Hochspannung-Mittelspannung 2023 | `faea6c7e4713d4ae93d34620876f5bac62dc66142d8455c095461c028a3ec53f` |
| Mittelspannung 2023 | `6142eab14f69ebcdc1b6798dfdd8756a7404f202729c16ff3d888a5dc356891e` |
| Mittelspannung-Niederspannung 2023 | `1857da9ce5663f38ef895026bc1d5381016371f09c224278f2ef309347726eb3` |
| Niederspannung 2023 | `e5accd071a68ec10aadcd2c36c6b58139eba1862e2b1f2018a1affbac676f025` |
| Netzverluste 2023 | `9c372896483e309811bd1f18a9b43045c2eb944126e4da872bece15a7185da5e` |
| Pronóstico SLP 2023 | `adf4442dd0cc27867e85ce0f323cb42c224152a990e01a396ada06e9fabd40cc` |
| Histórico de área de red XLSX | `f607d4267c270b2b6f22895b7f5a52c3077e7f61f1ceca73005e78d51e2fc1c9` |
