# Contrato de validación — reconstrucción horaria de Berlín

**Estado:** `preparado; sin ejecución externa`  
**Identificador:** `CORFO-MERLIN-EDM-DE-BERLIN-VALIDACION-01`  
**Fecha de corte:** 28 de septiembre de 2026  
**Caso:** Berlín, Alemania; reconstrucción histórica 2023

Este contrato define qué se valida, contra qué fuente, con qué unidad y qué
resultado puede declararse como evidencia del KPI. Separa la validación
temporal interna del modelo de la comparación con fuentes externas. Una fuente
oficial no se considera compatible si mide otra magnitud o tiene otro perímetro.

## 1. Objeto y perímetro

| Elemento | Definición operativa |
|---|---|
| Variable objetivo | Carga de red horaria derivada del perfil HV (*Hochspannung*, 110 kV) de Stromnetz Berlin |
| Naturaleza | Demanda de red; no se interpreta automáticamente como consumo final |
| Territorio | Berlín administrativo, AGS `11000`, usado como proxy del área HV mientras el operador no confirme la cartografía |
| Período piloto | Año calendario 2023 |
| Zona horaria | `Europe/Berlin` para presentación; `UTC` para las llaves de unión y cálculo |
| Resolución | 15 minutos en el insumo HV; 1 hora para entrenamiento, reconstrucción y comparación principal |
| Unidad | MW como carga media del intervalo; MWh para energía integrada |
| Meta operativa | MAPE horario menor o igual a 35 % sobre el conjunto de prueba temporal |

La serie HV se mantiene como `Stromnetz-Berlin-HV-area-proxy` hasta recibir una
confirmación explícita de alcance territorial y semántica. No se suman entre sí
los perfiles HV, MV, MV/LV y LV, porque representan niveles jerárquicos de la
misma red.

## 2. Capas de validación

### Capa A — validación temporal interna (KPI del modelo)

Se compara la reconstrucción contra observaciones reservadas del mismo perfil
HV. La partición es cronológica y no aleatoria: 70 % entrenamiento, 15 %
validación y 15 % prueba, según el contrato de entrenamiento alemán.

Indicadores obligatorios:

- MAPE, calculado solo para observaciones con referencia distinta de cero;
- MAE y RMSE en MW;
- sesgo medio y sesgo energético acumulado;
- error de la hora de máxima carga y error porcentual de la punta;
- cobertura: observaciones válidas respecto de las esperadas.

Esta capa es **interna** porque modelo y referencia proceden del mismo perfil
HV. Es la capa que se puede contrastar con el umbral MAPE ≤35 %, pero no prueba
por sí sola la equivalencia con el consumo final de Berlín.

### Capa B — consistencia anual externa

Se compara la energía anual reconstruida con la *Strombilanz* de
Amt für Statistik Berlin-Brandenburg. La referencia mide consumo final y
sectores, por lo que la comparación se reporta como consistencia externa
condicionada, no como MAPE horario.

Indicadores:

- energía anual modelada y publicada en MWh/GWh;
- diferencia absoluta de energía;
- sesgo energético porcentual;
- error absoluto relativo de energía;
- diferencia de participaciones sectoriales, cuando exista una desagregación
  compatible.

Si la Strombilanz o sus shares se utilizan para escalar, ponderar o construir
entradas del modelo, la fila debe marcar `dependencia_input=si` y no puede
presentarse como validación totalmente independiente.

### Capa C — consistencia espacial externa

Se agregará la reconstrucción a los distritos de Berlín y se comparará con el
consumo eléctrico anual del Umweltatlas. Esta capa evalúa distribución
territorial y no forma horaria.

Indicadores:

- cobertura de distritos comparables;
- correlación entre consumos distritales;
- MAE y RMSE de participaciones distritales;
- diferencia entre la participación modelada y la publicada;
- error de intensidad, solo si el denominador poblacional o territorial es
  idéntico.

El resultado debe conservar las exclusiones documentadas por Umweltatlas,
incluidas las celdas suprimidas por privacidad y la diferencia entre consumo
final, autoconsumo y pérdidas de red.

### Capa D — control horario de contexto

SMARD/ENTSO-E puede utilizarse para comparar la forma horaria agregada de
Alemania o de la zona de mercado. No es un comparador directo de Berlín porque
su perímetro no coincide con el área HV ni con el municipio.

Se compararán únicamente perfiles normalizados, por ejemplo restando la media
y dividiendo por la desviación estándar, y se reportarán correlación, error
normalizado y coincidencia de máximos. Esta capa es `contexto` y no puede
declarar el KPI contractual alemán.

### Capa E — comparador horario externo de Berlín (pendiente)

El comparador externo ideal sería una serie horaria agregada de consumo o carga
de Berlín proveniente de un comercializador, datos de liquidación, medidores
inteligentes anonimizados o un convenio institucional. Debe tener:

1. perímetro geográfico explícito;
2. definición de carga o energía y tratamiento de pérdidas;
3. cobertura temporal y porcentaje de medidores representados;
4. zona horaria y reglas para horario de verano;
5. revisiones, faltantes y procedimiento de anonimización;
6. licencia y autorización para reportabilidad.

Hasta obtenerlo, el KPI horario externo se mantiene `no evaluable`. No se debe
presentar la capa SMARD como sustituto de esta referencia.

## 3. Reglas de homologación

Antes de calcular cualquier indicador se debe verificar:

1. **Tiempo:** todas las llaves se convierten a UTC; las tablas de resultados
   conservan también la hora local y la marca DST.
2. **Resolución:** los datos de 15 minutos se agregan a una hora mediante
   promedio de carga para MW o suma de energía para MWh; no se mezclan ambas
   operaciones.
3. **Perímetro:** `11000` y el área de red HV se etiquetan por separado hasta que
   Stromnetz Berlin confirme su equivalencia.
4. **Semántica:** demanda de red, consumo final, pérdidas y autoconsumo se
   mantienen en columnas y comparaciones distintas.
5. **Cobertura:** se informa el denominador esperado, observaciones válidas,
   faltantes y cualquier imputación. En el piloto no se imputan faltantes sin
   una decisión documentada.
6. **Dependencia:** toda fuente usada para generar una entrada o escalar la
   salida se marca como condicionada en la matriz de evidencia.
7. **Reproducibilidad:** cada comparación conserva URL, fecha de acceso,
   versión/período, licencia, hash de entrada, hash de salida y commit.

## 4. Estructura mínima de datos

### Serie modelada o de red

```text
timestamp_utc,timestamp_local,dst_flag,territory_code,territory_name,
load_mw,energy_mwh,source,coverage_flag
```

### Referencia anual o sectorial

```text
year,territory_code,territory_name,sector,energy_mwh,
source,source_version,coverage_flag,exclusion_note
```

### Referencia espacial

```text
year,district_code,district_name,energy_mwh,share_pct,
source,privacy_flag,coverage_flag
```

Las columnas son un contrato de intercambio; no autorizan a rellenar valores
ausentes ni a inferir una semántica que la fuente no publique.

## 5. Decisión y evidencia

La comparación se clasifica como:

- `cumple`: indicador calculado, denominador compatible y criterio satisfecho;
- `no cumple`: indicador calculado y criterio no satisfecho;
- `no evaluable`: faltan datos, el denominador es cero o el perímetro/semántica
  no son comparables;
- `condicionada`: comparación útil, pero depende de una fuente usada para
  escala, shares o proxy territorial;
- `contexto`: control informativo sin validez para el KPI contractual.

Los resultados se registran en
[`comparaciones_externas_2023.csv`](../berlin/comparaciones_externas_2023.csv)
y, cuando exista una reconstrucción ejecutada, se incorporan a
`kpi_validation.csv`, `cumplimiento_kpi.md`, `ficha_evidencia_berlin.md` y
`manifiesto_berlin.json`.

## 6. Criterio de avance

La adaptación puede avanzar a la línea base si la capa A es reproducible y las
capas B y C tienen fuentes descargadas, transformaciones auditadas y cobertura
documentada. El cierre del KPI externo horario requiere además la capa E o una
justificación formal de por qué no fue posible obtenerla.
