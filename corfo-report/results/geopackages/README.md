# Exportaciones GeoPackage para ArcGIS

Se generó [`berlin_demanda_arcgis.gpkg`](berlin_demanda_arcgis.gpkg) como una copia de los resultados alemanes, sin modificar los CSV, Parquet ni GeoJSON originales.

El GeoPackage contiene:

| Elemento | Tipo | Registros | Uso |
|---|---|---:|---|
| `berlin_d8_district_annual` | Capa multipolígono | 60 | Demanda anual por distrito, 2020–2024 |
| `berlin_d8_district_sector_annual` | Capa multipolígono | 300 | Demanda anual por distrito-sector, 2020–2024 |
| `berlin_d8_annual_summary` | Tabla | 5 | Control anual agregado |
| `berlin_d8_hourly` | Tabla | 43.677 | Inferencia horaria vigente d=8 |
| `berlin_d3_hourly_historical` | Tabla | 8.740 | Línea base histórica d=3 |

Las capas espaciales usan `EPSG:25833` (ETRS89 / UTM 33N). Las magnitudes anuales están en GWh y las horarias en MW/MWh según el nombre del campo. Los campos temporales se mantienen como texto ISO 8601 para conservar explícitamente las representaciones UTC y local.

Las tablas horarias son no espaciales. Para visualizarlas en ArcGIS se pueden relacionar con una capa territorial mediante `id_bezirk` (capas anuales) o utilizar una tabla temporal agregada. No se duplicó la geometría por hora, porque eso produciría capas innecesariamente grandes.

Las capas distrito y distrito-sector son asignaciones condicionadas mediante pesos del Umweltatlas y shares de Strombilanz. Su exportación a GeoPackage no las convierte en mediciones espaciales independientes ni modifica el alcance de los KPI.

El detalle de rutas, conteos, hashes y limitaciones está en [`berlin_demanda_arcgis_manifest.json`](berlin_demanda_arcgis_manifest.json).

La definición completa de campos, tipos, unidades y claves de unión está en [`diccionario_campos_geopackages.md`](diccionario_campos_geopackages.md).

## Exportación chilena

La copia combinada chilena se encuentra fuera del repositorio Chile para mantenerlo intacto:

`/srv/compartido/inbox/MERLIN_EDM_GIS_exports/chile/chile_demanda_arcgis.gpkg`

Incluye las capas anuales regional y comunal ya existentes, además de las tres series horarias como tablas no espaciales. Su manifiesto está en el mismo directorio.
