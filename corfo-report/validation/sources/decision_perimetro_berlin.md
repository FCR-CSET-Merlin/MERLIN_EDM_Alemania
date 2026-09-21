# Decisión territorial del piloto de Berlín

**Fecha de decisión:** 21 de septiembre de 2026  
**Estado:** decisión operativa para el piloto; pendiente de confirmación semántica con Stromnetz Berlin  
**Caso:** reconstrucción histórica horaria de Berlín

## Problema que se resuelve

En las publicaciones de Stromnetz Berlin aparecen dos superficies que no deben tratarse como si fueran el mismo perímetro:

| Evidencia | Superficie | Interpretación para este proyecto |
|---|---:|---|
| Área servida en alta/media tensión, página vigente de Stromnetz Berlin | **891,12 km²** | Compatible con la superficie administrativa de Berlín y con la categoría HV que se está auditando |
| Superficie administrativa de Berlín, código territorial `11000` | **891,12 km²** | Perímetro operativo del piloto |
| Área geográfica del área de red, página EnWG vigente | **1.046,64 km²** | Métrica regulatoria del operador; no se dispone de un polígono público que permita usarla como frontera del modelo |
| Histórico de área de red de Stromnetz Berlin para 2023 | **891,12 km²** | Evidencia histórica coincidente con el perímetro administrativo |

La diferencia no se resolverá sumando o recortando series por una superficie. Una superficie publicada sin geometría no permite saber qué municipios, enclaves, corredores o áreas sin clientes están incluidos.

## Evidencia utilizada

1. [Stromnetz Berlin — publicación EnWG](https://www.stromnetz.berlin/uber-uns/veroffentlichungspflichten/energiewirtschaftsgesetz-enwg/): publica simultáneamente la superficie geográfica del área de red, el área servida en alta/media tensión y el histórico XLSX.
2. [Stromnetz Berlin — cifras y datos](https://www.stromnetz.berlin/uber-uns/zahlen-daten-fakten/): presenta 891,12 km² como superficie geográfica del área de red en la ficha general del operador.
3. [Berlin Open Data — Netzgebietsdaten](https://daten.berlin.de/datensaetze/netzgebietsdaten): identifica a Berlín como referencia geográfica del conjunto histórico de Stromnetz Berlin y enlaza `historie-netzgebietsdaten-berlin.xlsx`.
4. [Destatis GENESIS — área territorial](https://genesis.destatis.de/datenbank/online/statistic/11111/table/11111-0002/search/s/MTExMTE%3D) y [Amt für Statistik Berlin-Brandenburg](https://www.statistik-berlin-brandenburg.de/157-2024/): informan 891,12 km² para Berlín.
5. [BKG VG250](https://gdz.bkg.bund.de/index.php/default/wfs-verwaltungsgebiete-1-250-000-stand-01-01-wfs-vg250.html): fuente oficial de límites administrativos y códigos; se consultó el WFS `https://sgx.geodatenzentrum.de/wfs_vg250` para `vg250:vg250_krs`, `ars='11000'`.

## Geometría reproducible del perímetro operativo

La consulta BKG devolvió una entidad `MultiPolygon` con los siguientes atributos:

```text
ars/ags: 11000
gen: Berlin
bez: Kreisfreie Stadt
nuts: DE300
beginn: 2025-04-11
CRS: EPSG:25832 (ETRS89 / UTM zone 32N)
```

Consulta reproducible:

```text
https://sgx.geodatenzentrum.de/wfs_vg250?service=WFS&version=2.0.0&request=GetFeature&typeNames=vg250:vg250_krs&outputFormat=application%2Fjson&CQL_FILTER=ars%3D%2711000%27
```

El GeoJSON obtenido el 21-09-2026 tuvo SHA-256 `0c99a79f550cfe22badecf1ec03e40e393334c81acfa1d27aab5387e58874241`. GDAL calculó aproximadamente **893,02 km²** en EPSG:25832. Esta cifra se conserva como control de la geometría BKG y no reemplaza la superficie estadística de 891,12 km²: la diferencia puede provenir de generalización cartográfica, versión del límite y método de cálculo de superficie.

## Decisión para el modelo

Se fija el siguiente contrato territorial para la primera reconstrucción:

- **Perímetro de modelación:** Berlín administrativo, código `11000`, geometría BKG VG250.
- **Etiqueta del territorio:** `Berlin-administrative`.
- **Área nominal de reportabilidad:** 891,12 km², según las fuentes estadísticas y la ficha de Stromnetz Berlin.
- **Serie horaria candidata:** perfil de alta tensión de Stromnetz Berlin, etiquetado como `Stromnetz-Berlin-HV-area-proxy` hasta confirmar su semántica de carga agregada.
- **Relación entre ambos perímetros:** se acepta como proxy operativo porque el área servida HV/MV publicada por Stromnetz Berlin coincide en superficie con Berlín; no se declara que el polígono HV/MV sea idéntico al polígono administrativo.
- **Área 1.046,64 km²:** se conserva como indicador regulatorio separado (`Stromnetz-Berlin-geographic-network-area`) y no se usa para ampliar el polígono ni para calcular población, temperatura, consumo espacial o KPI.

Con esta decisión se puede avanzar en el piloto sin ocultar la incertidumbre: el KPI se reportará contra un territorio explícito y reproducible, y la fuente de red se identificará como un proxy de ese territorio.

## Caveat que permanece abierto

No se encontró un polígono público de Stromnetz Berlin que permita probar si los 1.046,64 km² corresponden a una frontera distinta, a una definición regulatoria más amplia o a una actualización metodológica. Antes de escalar a distritos, Länder o Alemania completa se debe solicitar al operador la definición cartográfica de `geografische Fläche des Netzgebietes` y confirmar qué perímetro cubren los archivos HV 2019–2023.

La ausencia de esa confirmación no bloquea el piloto de Berlín, pero impide llamar a la serie HV una medición exacta del área de red sin el calificativo `proxy`.

## Implicancias para la evaluación

- Las covariables territoriales se agregan dentro del límite BKG `11000`.
- Las series de red se conservan en su perímetro declarado por Stromnetz Berlin y se comparan como proxy, sin afirmar equivalencia exacta.
- Si el balance anual de Berlín usa otra definición —por ejemplo, consumo final o superficie estadística— se documentará como referencia de distinta naturaleza, no como validación independiente automática.
- El MAPE horario solo podrá declararse evaluable después de verificar cobertura temporal, zona `Europe/Berlin`, intervalos DST y semántica del perfil HV.

