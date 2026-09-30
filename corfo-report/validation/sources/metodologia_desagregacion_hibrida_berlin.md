# Desagregación híbrida distrito–sector de Berlín

Estado: diseño operativo inicial; no constituye todavía un KPI independiente.

**Decisión temporal del piloto:** `sector_share_temporal_resolution = annual_broadcast`. Los shares anuales se repiten durante las horas de 2023; la generación de perfiles mensuales queda como extensión opcional.

## Definición

La inferencia horaria agregada del modelo se conserva como magnitud de referencia:

\[
\hat L_{B,h} = \text{demanda horaria estimada para Berlín}.
\]

Para el piloto regional se utilizan shares anuales por distrito `d`, año `y` y sector `s`:

\[
w_{d,y}=\frac{E_{d,y}}{E_{B,y}}, \qquad
p_{d,y,s}=\frac{E_{d,y,s}}{\sum_s E_{d,y,s}}.
\]

La salida horaria distrito–sector se obtiene difundiendo esos pesos durante el año:

\[
\hat L_{d,h,s}=\hat L_{B,h}\,w_{d,y(h)}\,p_{d,y(h),s}.
\]

Los índices mensuales quedan reservados para una futura extensión comunal; no forman parte del contrato de entrenamiento de Berlín 2023.

Para el piloto regional se comprobará que la suma de distritos y sectores conserve el total anual agregado. No se calculan shares mensuales en la entrada de la red; la matriz distrito–sector se reporta como salida anual.

## Implementación por niveles de datos

1. Para el piloto actual, se usa la matriz anual distrito–sector y se difunden sus shares a todas las horas del año.
2. Si en una fase posterior se requiere una capa comunal alemana mensual, se podrán introducir perfiles sectoriales normalizados.
3. Si solo existe consumo anual por distrito, se usa la matriz de proxies territorializados y se ajusta mediante un raking proporcional restringido para que coincidan los totales distritales y los totales sectoriales de Berlín.

La matriz restringida se obtiene minimizando la divergencia relativa respecto de los proxies, con restricciones de suma por distrito y por sector. Los valores negativos se prohíben y los ceros estructurales se mantienen como ceros.

## Fuentes actualmente disponibles

- `berlin_umweltatlas_bezirke_2023.csv`: total anual por los 12 distritos; se usa inicialmente para `w_d`.
- `berlin_umweltatlas_bezirke_detail_2023.csv`: categorías `verbr_gewerbe`, `verbr_haushalt`, `verbr_nachtspeicher`, `verbr_waermepumpe` y `verbr_lastgangkunde`; son proxies, no equivalentes directos a los cinco sectores chilenos.
- `berlin_sector_shares_2023.csv`: shares anuales agregados de Berlín provenientes de Strombilanz; no son shares mensuales ni distritales.

La primera corrida será, por tanto, un escenario híbrido condicionado. `verbr_lastgangkunde` no se interpretará automáticamente como industria: se repartirá entre industria y comercio mediante la restricción de los totales sectoriales de Berlín. El transporte se mantendrá como categoría separada y requerirá una proxy territorial específica antes de declararse validado.

## Limitaciones y validación

Los perfiles BDEW/SLP y las variables proxy quedan fuera del contrato temporal del piloto; podrían usarse en una extensión mensual, pero no son necesarios para la reconstrucción regional 2023. La validación espacial independiente requiere observaciones distritales que no hayan sido usadas como pesos. Toda salida debe conservar `source`, `mapping_policy`, `imputation_flag`, `spatial_perimeter` y `sector_share_temporal_resolution`.
