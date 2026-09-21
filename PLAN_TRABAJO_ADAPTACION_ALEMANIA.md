# Plan de trabajo — adaptación de MERLIN EDM a Alemania

**Caso piloto:** reconstrucción histórica de demanda eléctrica para Berlín
**Estado:** planificación y evaluación de factibilidad; no se declara ningún KPI alemán cumplido.
**Reportabilidad activa:** [`corfo-report/`](corfo-report/README.md)
**Referencia heredada de Chile:** [`corfo-report-chile-referencia/`](corfo-report-chile-referencia/README.md)

## 1. Objetivo y alcance

El objetivo inicial es obtener una reconstrucción histórica horaria para Berlín y comprobar si la metodología desarrollada para Chile puede operar con fuentes alemanas. La red neuronal chilena se conserva como línea base técnica, pero no se asumen transferibles sus pesos ni sus definiciones sectoriales. El modelo alemán debe homologar variables, unidades, fronteras territoriales, calendario y fuentes de consumo antes de entrenarse o evaluarse.

La carpeta `corfo-report/` contiene exclusivamente resultados y evidencia de Alemania. Los archivos chilenos heredados se conservan en `corfo-report-chile-referencia/` y no cuentan como evidencia del piloto alemán.

## 2. Variable objetivo y referencia anual

Se deben mantener separadas dos magnitudes:

1. **Demanda retirada desde la red:** candidata principal para la serie horaria, medida en el perímetro de un operador o área de red.
2. **Consumo final:** referencia apropiada para balances anuales y sectores, pero no necesariamente una medición horaria completa.

La primera implementación usará demanda de red como objetivo horario y consumo final como referencia anual, siempre que se documente su relación. Autoconsumo, pérdidas, almacenamiento, generación distribuida y diferencias de perímetro deben quedar registrados como limitaciones o ajustes explícitos.

## 3. Fuentes potenciales y factibilidad

`Candidata` significa que la fuente fue identificada, no que ya haya sido descargada, validada o aceptada como comparador.

| Fuente | Variable | Escala/resolución | Uso | Estado inicial | Verificación obligatoria |
|---|---|---|---|---|---|
| [Stromnetz Berlin](https://www.stromnetz.berlin/uber-uns/veroffentlichungspflichten/energiewirtschaftsgesetz-enwg/) | Carga de red, carga residual y perfiles | Área de red; archivos y potencialmente 15 min | Objetivo horario | Candidata principal | Año completo, unidades, zona horaria, faltantes y perímetro |
| [Statistik Berlin-Brandenburg](https://www.statistik-berlin-brandenburg.de/e-iv-4-j/) | Balance eléctrico y consumo final sectorial | Berlín; anual | Referencia anual | Alta para anual | Definiciones, revisiones, unidades y exclusiones |
| [Umweltatlas Berlin](https://daten.berlin.de/datensaetze/energieverbrauch-strom-umweltatlas-wfs-238921d9) | Consumo eléctrico territorial | Distritos y bloques; anual | Distribución espacial | Media/alta | Privacidad, cobertura y compatibilidad de límites |
| [SMARD](https://www.smard.de/page/en/wiki-article/6078/6036/electricity-consumption) | Uso efectivo desde red | Alemania; 15 min | Contexto nacional | Media para Berlín | Desagregación territorial; no asumir equivalencia local |
| [DWD](https://www.dwd.de/EN/ourservices/cdc/cdc.html?lsbId=646268) / [ERA5-Land](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=documentation) | Temperatura y clima | Estación/grilla; horaria | Variables exógenas | Alta | Versión, cobertura y zona horaria |
| [Zensus 2022](https://www.destatis.de/zensus2022?nn=1344278) | Población y vivienda | Grilla/territorio; censal | Covariables estructurales | Media | Licencia, nivel geográfico y compatibilidad temporal |
| [Destatis/GENESIS](https://www.destatis.de/EN/Service/OpenData/api-webservice.html) | Población, actividad y energía | Varios territorios; variable | Covariables y controles | Media/alta | Tabla, versión, unidad y nivel geográfico |
| [Agencia Federal de Empleo](https://statistik.arbeitsagentur.de/DE/Navigation/Statistiken/Fachstatistiken/Beschaeftigung/Beschaeftigte/Beschaeftigte-Nav.html) | Empleo y actividad | Territorios; mensual/anual | Variables de actividad | Media | Sectores WZ y cobertura distrital |
| [BDEW](https://www.bdew.de/media/documents/2025-03-17_AWH_Aktualisierte_SLP_Strom_2025_Ver%C3%B6ffentlichung.pdf) | Perfiles estándar | Tipos de consumidor; horario | Línea base/prior | Media como prior | No usar como validación independiente |
| [BKG VG250](https://gdz.bkg.bund.de/index.php/default/wfs-verwaltungsgebiete-1-250-000-stand-01-01-wfs-vg250.html) | Límites y códigos | Alemania; administrativo | Homologación espacial | Alta | Año de límites, CRS y correspondencia con red |
| [DemandRegio](https://opendata.ffe.de/project/demandregio/) | Regionalizaciones modeladas | Alemania; variable | Comparador secundario | Media | Marcar como modelada, no como referencia independiente |

Antes de aceptar una fuente se debe registrar URL, responsable, fecha de acceso, versión/licencia, unidad, definición, cobertura, zona horaria, perímetro, transformaciones, archivo original, SHA-256 y dependencia respecto del balance usado para escalar.

## 4. Fases y pasos

### Fase 0 — Auditoría de factibilidad y contrato de datos

1. Confirmar repositorio, commit y entorno Python/ML.
2. Levantar fichas de cada fuente y conservar sus hashes.
3. Inspeccionar los archivos de Stromnetz Berlin y comprobar si contienen años completos.
4. Determinar si el área de red coincide con Berlín o declarar el objetivo como `Stromnetz-Berlin-area`.
5. Comparar demanda de red, consumo final, pérdidas y autoconsumo.
6. Fijar `Europe/Berlin` para fuentes y UTC para uniones internas, conservando las horas DST repetidas/ausentes.
7. Elegir el período común; `2019–2023` es candidato hasta verificar cobertura.

**Producto:** inventario de fuentes, hashes y dictamen `GO`, `GO condicionado` o `NO-GO` en `corfo-report/validation/sources/`.

### Fase 1 — Homologación territorial, sectorial y temporal

1. Fijar Berlín como ciudad y estado federado, con sus 12 distritos.
2. Construir correspondencia entre área de red, municipio, distritos y códigos VG250.
3. Usar inicialmente hogares, industria, comercio/servicios (incluido sector público) y transporte.
4. No separar Comercial/Público si no existe una referencia comparable; documentar la agrupación GHD.
5. Homologar MW medios por intervalo, MWh, kWh y GWh.
6. Verificar años bisiestos, cambios DST y unicidad de timestamps.

**Producto:** contrato de datos y tabla de correspondencias.

### Fase 2 — Línea base y adaptación

1. Congelar una ejecución de referencia del modelo chileno, columnas y pesos.
2. Mapear variables alemanas y registrar las que no tengan equivalente.
3. Comparar perfil estándar, modelo chileno sin ajuste y modelo alemán reentrenado/recalibrado.
4. Reentrenar si cambia la variable objetivo, sectorización o distribución climática.
5. Separar parámetros aprendidos, físicos, shares observados e imputaciones.

**Producto:** configuración reproducible y tabla de diferencias Chile–Alemania.

### Fase 3 — Reconstrucción histórica de Berlín

1. Preparar demanda, temperatura, calendario, sectores y covariables.
2. Crear particiones temporales sin fuga de información.
3. Ejecutar inferencia para Berlín y, si existe referencia anual, para distritos.
4. Agregar intervalos a horas y horas a día/mes/año conservando unidades.
5. Guardar series pesadas fuera de Git y registrar ruta, tamaño y hash.

**Producto:** tablas, figuras, series indexadas y manifiesto del caso Berlín.

### Fase 4 — Validación y evidencia KPI

1. Contrastar el perfil horario con una fuente de red independiente del escalamiento.
2. Contrastar consumo anual total y sectorial con el balance oficial.
3. Calcular MAPE, MAE, RMSE y cobertura con denominador explícito.
4. Informar todos los años, sectores y territorios; no ocultar incumplimientos.
5. Generar CSV, Markdown y manifiesto JSON.
6. Revisar manualmente la ficha antes de escribir `cumple`.

**Producto:** `kpi_validation.csv`, `kpi_summary.csv`, `cumplimiento_kpi.md`, `ficha_evidencia_berlin.md` y `manifiesto_berlin.json`.

### Fase 5 — Escalamiento

Tras cerrar Berlín, evaluar distritos, Länder y Alemania completa. La expansión requiere que el contrato de datos, la frontera territorial y la evidencia KPI sean reproducibles en el piloto.

## 5. KPI y reglas de evidencia

La meta operativa del piloto es **MAPE menor o igual a 35 %**. La ficha debe conservar además el criterio literal de la matriz contractual CORFO si esta exige `<35 %`; ambos criterios no deben confundirse.

Cada fila de `kpi_validation.csv` debe incluir:

`id_evidencia`, `compromiso`, `indicador`, `pais`, `territorio`, `nivel`, `año`, `sector`, `n_observaciones`, `n_validas`, `mape_pct`, `mae`, `rmse`, `umbral_pct`, `criterio`, `cumple_umbral`, `comparador`, `comparador_independiente`, `dependencia_input`, `fuente_referencia`, `hash_entrada`, `hash_salida`.

La evidencia queda incompleta si falta la referencia, fórmula, cobertura, modelo/commit, fuentes, hashes, limitaciones o resultado explícito `cumple`, `no cumple` o `no evaluable`.

Si el balance anual se usa para shares o escala, la comparación contra ese balance se etiqueta como **consistencia condicionada**, no como validación independiente. La validación horaria requiere una referencia de red independiente o una relación documentada.

## 6. Estructura activa de reportabilidad

```text
corfo-report/
├── README.md
├── results/
│   ├── figures/
│   ├── tables/
│   └── timeseries/
└── validation/
    ├── figures/
    ├── sources/
    ├── berlin/
    ├── kpi_plan.md
    ├── ficha_evidencia_berlin.md
    ├── cumplimiento_kpi.md
    └── manifiesto_berlin.json
```

Los datasets pesados y descargas originales no se versionan. Sí se versionan tablas pequeñas, figuras, fichas, manifiestos e índices de hashes. Cada corrida tendrá `run_id`, fecha de corte, commit y entradas/salidas.

## 7. Criterio de avance

No se declara factibilidad plena hasta verificar una serie horaria utilizable y un perímetro defendible. No se declara cumplimiento hasta ejecutar el modelo, generar el CSV y revisar la ficha. Si Stromnetz Berlin no ofrece una serie anual completa o no puede reconciliarse su perímetro, se debe declarar la brecha horaria y limitar el objetivo a validación anual.
