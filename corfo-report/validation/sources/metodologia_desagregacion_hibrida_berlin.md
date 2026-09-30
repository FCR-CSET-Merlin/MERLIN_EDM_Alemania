# Desagregación híbrida distrito–sector de Berlín

Estado: diseño operativo inicial; no constituye todavía un KPI independiente.

## Definición

La inferencia horaria agregada del modelo se conserva como magnitud de referencia:

\[
\hat L_{B,h} = \text{demanda horaria estimada para Berlín}.
\]

Para cada distrito `d`, mes `m` y sector `s` se utilizarán dos familias de pesos:

\[
w_{d,m}=\frac{E_{d,m}}{E_{B,m}}, \qquad
p_{d,m,s}=\frac{E_{d,m,s}}{\sum_s E_{d,m,s}}.
\]

La salida distrito–sector será:

\[
\hat L_{d,h,s}=\hat L_{B,h}\,w_{d,m(h)}\,p_{d,m(h),s}.
\]

Cada mes se comprobará que la suma de distritos y sectores conserve el total agregado, dentro de la tolerancia numérica definida en el contrato de datos.

## Implementación por niveles de datos

1. Si existe consumo mensual distrito–sector, `w` y `p` se calculan directamente.
2. Si existen consumos anuales distrito–sector, se conserva la matriz anual y se aplican perfiles mensuales sectoriales alemanes normalizados.
3. Si solo existe consumo anual por distrito, se usa la matriz de proxies territorializados y se ajusta mediante un raking proporcional restringido para que coincidan los totales distritales y los totales sectoriales de Berlín.

La matriz restringida se obtiene minimizando la divergencia relativa respecto de los proxies, con restricciones de suma por distrito y por sector. Los valores negativos se prohíben y los ceros estructurales se mantienen como ceros.

## Fuentes actualmente disponibles

- `berlin_umweltatlas_bezirke_2023.csv`: total anual por los 12 distritos; se usa inicialmente para `w_d`.
- `berlin_umweltatlas_bezirke_detail_2023.csv`: categorías `verbr_gewerbe`, `verbr_haushalt`, `verbr_nachtspeicher`, `verbr_waermepumpe` y `verbr_lastgangkunde`; son proxies, no equivalentes directos a los cinco sectores chilenos.
- `berlin_sector_shares_2023.csv`: shares anuales agregados de Berlín provenientes de Strombilanz; no son shares mensuales ni distritales.

La primera corrida será, por tanto, un escenario híbrido condicionado. `verbr_lastgangkunde` no se interpretará automáticamente como industria: se repartirá entre industria y comercio mediante la restricción de los totales sectoriales de Berlín. El transporte se mantendrá como categoría separada y requerirá una proxy territorial específica antes de declararse validado.

## Limitaciones y validación

Los perfiles BDEW/SLP y las variables proxy sirven para asignar energía, no para validar independientemente la red neuronal. La validación espacial independiente requiere observaciones distritales que no hayan sido usadas como pesos. Toda salida debe conservar `source`, `mapping_policy`, `imputation_flag`, `spatial_perimeter` y `temporal_profile_source`.
