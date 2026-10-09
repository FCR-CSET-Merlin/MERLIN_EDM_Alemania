# Diccionario de campos y ubicaciones de los GeoPackage

Este documento describe la estructura de las copias GeoPackage preparadas para ArcGIS y mantiene la trazabilidad hacia los archivos originales. La exportación no modifica Parquet, CSV, CSV comprimidos, GeoJSON ni GeoPackage de origen.

## Archivos GeoPackage

| Caso | GeoPackage | Tamaño aproximado | CRS de las capas espaciales | Ubicación |
|---|---|---:|---|---|
| Alemania, Berlín | `berlin_demanda_arcgis.gpkg` | 24 MB | EPSG:25833, ETRS89 / UTM 33N | [`corfo-report/results/geopackages/berlin_demanda_arcgis.gpkg`](berlin_demanda_arcgis.gpkg) |
| Chile, copia combinada | `chile_demanda_arcgis.gpkg` | 1,6 GB | EPSG:4326, WGS 84 | [`/srv/compartido/inbox/MERLIN_EDM_GIS_exports/chile/chile_demanda_arcgis.gpkg`](/srv/compartido/inbox/MERLIN_EDM_GIS_exports/chile/chile_demanda_arcgis.gpkg) |

El GeoPackage chileno se encuentra fuera del repositorio `MERLIN_EDM` para mantenerlo intacto. Su manifiesto externo es [`chile_demanda_arcgis_manifest.json`](/srv/compartido/inbox/MERLIN_EDM_GIS_exports/chile/chile_demanda_arcgis_manifest.json). El manifiesto alemán, con hashes de entradas y salidas, está en [`berlin_demanda_arcgis_manifest.json`](berlin_demanda_arcgis_manifest.json).

## GeoPackage alemán

### Capa `berlin_d8_district_annual`

Es una capa multipolígono con 60 entidades: 12 distritos × 5 años (2020–2024). Cada distrito aparece una vez por año.

| Campo | Tipo | Descripción | Unidad/uso |
|---|---|---|---|
| `fid` | entero | Identificador técnico de la entidad GeoPackage. | Interno |
| `geom` | multipolígono | Geometría del distrito de Berlín. | EPSG:25833 |
| `year` | entero | Año de la reconstrucción. | 2020–2024 |
| `id_bezirk` | entero | Código del distrito (`Bezirk`). | Clave para unir tablas |
| `bezirk` | texto | Nombre del distrito. | Ej.: Mitte |
| `city_predicted_GWh` | real | Demanda anual predicha para Berlín antes de desagregar. | GWh |
| `district_weight_2023` | real | Peso territorial fijo utilizado para el distrito. | Proporción; suma 1 entre distritos |
| `district_predicted_GWh` | real | Demanda anual asignada al distrito. | GWh |
| `allocation_rule` | texto | Regla aplicada: predicción Berlín × peso distrital Umweltatlas 2023. | Metadato metodológico |
| `spatial_status` | texto | Estado interpretativo de la capa. | `conditional_allocation_not_independent_kpi` |

### Capa `berlin_d8_district_sector_annual`

Es una capa multipolígono con 300 entidades: 12 distritos × 5 años × 5 sectores. La geometría se repite para cada combinación año-sector.

Incluye todos los campos anteriores y los siguientes:

| Campo | Tipo | Descripción | Unidad/uso |
|---|---|---|---|
| `sector_code` | texto | Código sectorial. | `I`, `R`, `C`, `P`, `T` |
| `sector_name` | texto | Nombre del sector. | Industria y minería; Residencial; Comercio/GHD; Público; Transporte |
| `sector_share_annual` | real | Share sectorial anual de Strombilanz. | Proporción |
| `district_sector_predicted_GWh` | real | Demanda anual asignada al distrito-sector. | GWh |
| `allocation_rule` | texto | Peso distrital 2023 × share sectorial anual. | Metadato metodológico |
| `spatial_sector_status` | texto | Estado interpretativo de la asignación. | `conditional_allocation_not_independent_kpi` |

El sector `P` aparece con share cero en la versión actual porque la fuente Strombilanz utilizada no permite separar consumo público de forma identificable.

### Tablas alemanas no espaciales

Estas tablas no contienen `geom` ni CRS. En ArcGIS se agregan como tablas y pueden filtrarse, exportarse o relacionarse con capas espaciales.

#### `berlin_d8_annual_summary` — 5 registros

| Campo | Tipo | Descripción | Unidad |
|---|---|---|---|
| `year` | entero | Año. | Año calendario |
| `split` | texto | Partición contractual. | `train`, `validation` o `test` |
| `n_complete_hours` | entero | Horas con ocho rezagos térmicos completos. | Horas |
| `observed_energy_GWh` | real | Energía HV observada en filas completas. | GWh |
| `predicted_energy_GWh` | real | Energía predicha por d=8. | GWh |
| `predicted_minus_observed_pct` | real | Diferencia relativa predicción-observación. | % |
| `sector_share_sum_error` | real | Error de suma de shares sectoriales respecto de 1. | Proporción |
| `share_status` | texto | Estado de los shares del año. | Metadato |
| `district_total_residual_GWh` | real | Residuo de conservación tras repartir por distrito. | GWh |
| `district_sector_total_residual_GWh` | real | Residuo de conservación tras repartir por distrito-sector. | GWh |

#### `berlin_d8_hourly` — 43.677 registros

Es la inferencia horaria vigente del modelo multianual d=8 para el agregado HV de Berlín.

| Campo | Tipo | Descripción | Unidad/uso |
|---|---|---|---|
| `source_year` | entero | Año de la observación. | 2020–2024 |
| `timestamp_hour_end_utc` | texto | Fin de hora en UTC. | ISO 8601 |
| `timestamp_hour_end_local` | texto | Fin de hora en horario local de Berlín. | ISO 8601 |
| `load_mean_MW` | real | Carga HV observada. | MW |
| `energy_MWh` | real | Energía observada de la hora. | MWh |
| `split` | texto | Partición cronológica. | `train`, `validation` o `test` |
| `load_predicted_MW` | real | Carga estimada por el MLP d=8. | MW |
| `prediction_error_MW` | real | Predicción menos observación. | MW |
| `coverage_flag` | texto | Indicador de completitud de los ocho rezagos. | `complete_d8_features` |

#### `berlin_d3_hourly_historical` — 8.740 registros

Es la salida horaria histórica de la línea base d=3 de 2023. No corresponde a la versión reportable vigente.

| Campo | Tipo | Descripción | Unidad/uso |
|---|---|---|---|
| `timestamp_hour_end_utc`, `timestamp_hour_end_local` | texto | Fin de hora en UTC y Berlín local. | ISO 8601 |
| `territory_code` | entero | Código territorial administrativo de Berlín. | `11000` |
| `territory_name` | texto | Nombre del territorio. | Berlin |
| `load_observed_MW`, `load_predicted_MW` | real | Carga observada y predicha. | MW |
| `energy_observed_MWh`, `energy_predicted_MWh` | real | Energía observada y predicha. | MWh |
| `residual_MW`, `residual_pct` | real | Error absoluto y relativo firmado. | MW y % |
| `split` | texto | Partición de la línea base. | train/validation/test |
| `coverage_flag` | texto | Completitud de variables d=3. | Metadato |
| `model_dimension` | entero | Número de rezagos térmicos. | 3 |
| `model_weight` | texto | Ruta relativa al archivo de pesos `.keras`. | Metadato |

## GeoPackage chileno

### Capa `wp2_output_demanda_electrica_regional`

Es una capa multipolígono con 32 entidades: 16 regiones × los años 2024 y 2025.

| Campo | Tipo | Descripción | Unidad/uso |
|---|---|---|---|
| `fid`, `geom` | técnico | Identificador y geometría. | EPSG:4326 |
| `objectid` | entero | Identificador de la geometría original. | Interno |
| `cod_region` | entero | Código de región. | Clave territorial |
| `region` | texto | Nombre de la región. | Ej.: TARAPACÁ |
| `shape_length`, `shape_area` | real | Atributos geométricos heredados. | Revisar CRS antes de interpretarlos como unidades métricas |
| `año` | entero | Año del agregado. | 2024 o 2025 |
| `demanda_total_GWh` | real | Demanda eléctrica total estimada. | GWh |
| `demanda_R_GWh` | real | Demanda residencial. | GWh |
| `demanda_C_GWh` | real | Demanda comercial. | GWh |
| `demanda_P_GWh` | real | Demanda pública. | GWh |
| `demanda_I_GWh` | real | Demanda industrial. | GWh |
| `demanda_T_GWh` | real | Demanda de transporte. | GWh |

### Capa `wp2_output_demanda_electrica_comunal`

Es una capa multipolígono con 690 entidades: 345 comunas × los años 2024 y 2025.

| Campo | Tipo | Descripción | Unidad/uso |
|---|---|---|---|
| `fid`, `geom` | técnico | Identificador y geometría. | EPSG:4326 |
| `objectid`, `cut` | entero | Identificadores de la geometría/comuna. | Claves territoriales |
| `cod_region` | entero | Código de región. | Clave territorial |
| `region_x`, `region_y` | texto | Atributos regionales conservados del cruce espacial. | Texto |
| `cod_provincia` | entero | Código de provincia. | Clave territorial |
| `provincia` | texto | Nombre de provincia. | Texto |
| `comuna` | texto | Nombre de comuna. | Clave de unión nominal |
| `shape_length`, `shape_area` | real | Atributos geométricos heredados. | Revisar CRS antes de interpretarlos como unidades métricas |
| `año` | entero | Año del agregado. | 2024 o 2025 |
| `demanda_total_GWh`, `demanda_R_GWh`, `demanda_C_GWh`, `demanda_P_GWh`, `demanda_I_GWh`, `demanda_T_GWh` | real | Demanda total y demanda por sector. | GWh |

### Tablas horarias chilenas

Las tres tablas son no espaciales y conservan las series horarias originales en MWh.

| Tabla | Registros | Campos territoriales | Campos de demanda |
|---|---:|---|---|
| `chile_regional_hourly_2023` | 140.160 | `timestamp`, `year`, `region`, `region_bne` | `demand_total_MWh`, `demand_R_MWh`, `demand_C_MWh`, `demand_P_MWh`, `demand_I_MWh`, `demand_T_MWh` |
| `chile_regional_hourly_2024_2025` | 280.704 | `timestamp`, `region` | `demand_MWh`, `demand_R_mwh`, `demand_C_mwh`, `demand_P_mwh`, `demand_I_mwh`, `demand_T_mwh` |
| `chile_comunal_hourly_2024_2025` | 6.052.680 | `timestamp`, `region`, `comuna` | `demand_MWh`, `demand_R_mwh`, `demand_C_mwh`, `demand_P_mwh`, `demand_I_mwh`, `demand_T_mwh` |

En estas tablas `timestamp` es texto y representa el inicio de la hora en los archivos originales. Para usar el control temporal de ArcGIS conviene convertirlo a un campo Date, conservando el texto original como respaldo.

## Archivos originales y ubicaciones

### Alemania

| Insumo o resultado original | Ubicación |
|---|---|
| Geometría de los 12 distritos | [`berlin_strom_districts.geojson`](../../../prototipo_3/data/de_alemania/external_validation/berlin_2023/berlin_strom_districts.geojson) |
| Tabla anual por distrito | [`berlin_multiyear_d8_district_annual.csv`](../tables/berlin_multiyear_d8_district_annual.csv) |
| Tabla anual distrito-sector | [`berlin_multiyear_d8_district_sector_annual.csv`](../tables/berlin_multiyear_d8_district_sector_annual.csv) |
| Resumen anual | [`berlin_multiyear_d8_annual_summary.csv`](../tables/berlin_multiyear_d8_annual_summary.csv) |
| Inferencia horaria vigente d=8 | [`berlin_multiyear_d8_inference.csv.gz`](../../../prototipo_3/data/de_alemania/berlin_multiyear_inference_d8/berlin_multiyear_d8_inference.csv.gz) |
| Inferencia histórica d=3 | [`berlin_d3_inference_2023.csv`](../../../prototipo_3/data/de_alemania/berlin_inference_2023/berlin_d3_inference_2023.csv) |
| Contratos Parquet de entrenamiento d=3/d=5/d=8 | `prototipo_3/data/de_alemania/berlin_training_multiyear/` |

### Chile

| Insumo o resultado original | Ubicación |
|---|---|
| GeoPackage regional anual original | [`wp2_output_demanda_electrica_regional.gpkg`](/srv/compartido/inbox/datos_modelos_MERLIN_EDM_prot_3/data/rec_2024_2025/results/capas_regionales/wp2_output_demanda_electrica_regional.gpkg) |
| GeoPackage comunal anual original | [`wp2_output_demanda_electrica_comunal.gpkg`](/srv/compartido/inbox/datos_modelos_MERLIN_EDM_prot_3/data/rec_2024_2025/results/capas_comunales/wp2_output_demanda_electrica_comunal.gpkg) |
| Serie regional horaria 2023 | [`demanda_regional_2023_horaria.parquet`](/srv/compartido/inbox/MERLIN_EDM/prototipo_3/data/rec_historica/2023/demanda_regional_2023_horaria.parquet) |
| Serie regional horaria 2024–2025 | [`wp2_output_demanda_electrica_regional_ts.parquet`](/srv/compartido/inbox/datos_modelos_MERLIN_EDM_prot_3/data/rec_2024_2025/results/capas_regionales/wp2_output_demanda_electrica_regional_ts.parquet) |
| Serie comunal horaria 2024–2025 | [`wp2_output_demanda_electrica_comunal_ts.parquet`](/srv/compartido/inbox/datos_modelos_MERLIN_EDM_prot_3/data/rec_2024_2025/results/capas_comunales/wp2_output_demanda_electrica_comunal_ts.parquet) |

## Uso recomendado en ArcGIS

1. Agregar el GeoPackage desde **Catalog > Databases > Add Database**.
2. Para mapas anuales, agregar directamente las capas `berlin_d8_district_annual`, `berlin_d8_district_sector_annual`, `wp2_output_demanda_electrica_regional` o `wp2_output_demanda_electrica_comunal`.
3. Usar `year`/`año` como filtro temporal y `id_bezirk`, `cod_region`, `comuna` o `cut` como claves territoriales.
4. Agregar las tablas horarias como tablas independientes. Para mapear una hora específica, filtrar la tabla y relacionarla con la geometría correspondiente.
5. Mantener la unidad: MWh para series horarias y GWh para capas anuales.

Las capas alemanas distrito y distrito-sector son asignaciones condicionadas por proxies espaciales y sectoriales. El campo `spatial_status` o `spatial_sector_status` debe conservarse al publicar mapas para evitar interpretar esos valores como mediciones distritales independientes.
