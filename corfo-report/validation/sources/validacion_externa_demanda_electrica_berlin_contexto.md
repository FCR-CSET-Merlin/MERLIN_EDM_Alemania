# Validación externa de un modelo horario de demanda eléctrica para Berlín

**Documento de contexto para continuar el modelo eléctrico**
**Fecha de revisión:** 29 de septiembre de 2026
**Territorio objetivo:** Berlín administrativo, código 11000
**Año piloto:** 2023
**Resolución del modelo:** horaria
**Variable objetivo:** carga eléctrica agregada de Berlín
**Modelo descrito:** MLP con temperatura y variables de calendario
**Serie de entrenamiento:** carga HV publicada por Stromnetz Berlin

## 1. Propósito y conclusión ejecutiva

Este documento reúne fuentes públicas, oficiales y académicas que pueden apoyar la validación o contextualización de una reconstrucción horaria de carga eléctrica para Berlín.

La búsqueda no encontró una serie pública, medida por una entidad independiente y con perímetro exactamente igual al Berlín administrativo (11000), que permita validar hora a hora la carga agregada de 2023. La evidencia más defendible se compone de tres contrastes distintos:

1. **Magnitud anual independiente:** comparar la energía integrada del modelo con el consumo final eléctrico anual de Berlín publicado en el balance energético oficial. Esto valida el orden de magnitud anual, después de explicar la diferencia entre consumo final y carga medida en HV.
2. **Generalización temporal:** aplicar el modelo ya congelado a 2022 o 2024 y contrastar con otra curva HV de Stromnetz Berlin. Es una evaluación fuera de muestra temporal, pero no independiente del operador ni de la familia de medición usada para entrenar.
3. **Distribución espacial anual:** usar el consumo de electricidad por bloques, distritos y códigos postales del Energieatlas Berlin (2022) como comprobación territorial, con cautela por el año, la cobertura y la posible procedencia común de los datos.

Las curvas de SMARD, ENTSO-E y 50Hertz no representan Berlín: son agregados nacionales, zonas de control o zonas de oferta. Pueden servir como contexto de forma y eventos, pero no como verdad de terreno berlinesa.

## 2. Criterios de lectura y clasificación

- **A — Apta para KPI externo independiente:** mide un aspecto pertinente con procedencia independiente. La escala debe especificarse; una fuente anual no valida errores horarios.
- **B — Apta solo para validación temporal:** permite prueba fuera del año de entrenamiento, pero no es independiente del origen del dato o del perímetro.
- **C — Apta como control de forma o contexto:** contrasta tendencias, magnitudes parciales, distribución espacial o contexto de sistema, sin medir directamente la carga objetivo.
- **D — No apta para validación:** representa una variable conceptual o geográfica que no corresponde a la demanda observada objetivo.

La etiqueta asignada es deliberadamente conservadora. «Publicada por otro organismo» no significa por sí sola «independiente»: hay que distinguir quién publica la serie de quién la midió o calculó y qué perímetro representa.

## 3. Fuentes prioritarias

### 3.1 Balance energético oficial de Berlín — Amt für Statistik Berlin-Brandenburg

- **Dataset y responsable:** *Energie- und CO₂-Bilanz in Berlin und Brandenburg*, Amt für Statistik Berlin-Brandenburg, metodología del Länderarbeitskreis Energiebilanzen.
- **Acceso:** [Portal y tablas descargables XLSX/PDF, serie E IV 4-j](https://www.statistik-berlin-brandenburg.de/e-iv-4-j/)
- **Cobertura:** Land Berlin; la publicación también informa Brandenburg en tablas separadas.
- **Resolución y período:** anual; hay serie histórica y resultado definitivo de 2023.
- **Dato de 2023:** consumo de electricidad de Berlín = **42.409 TJ**, equivalente a **11.780,3 GWh** o **11.780.278 MWh** (conversión: 1 TJ = 277,777… MWh).
- **Unidad y concepto:** energía anual consumida en el balance energético; no es una curva de potencia ni equivale necesariamente a la energía que atraviesa un punto de medición HV.
- **Medición/estimación:** balance estadístico anual armonizado por la metodología del Länderarbeitskreis Energiebilanzen. No ofrece lecturas horarias.
- **Zona horaria/DST:** no aplica a agregados anuales.
- **Licencia:** el sitio declara CC BY 3.0 Alemania para el contenido.
- **Estabilidad/reproducibilidad:** alta; hay página institucional, archivos descargables y publicaciones archivables.
- **Compatibilidad con HV de Stromnetz Berlin:** parcial. El balance informa consumo final, mientras una curva HV de red puede reflejar flujos y pérdidas con un perímetro de medición diferente. Autoconsumo detrás del contador y otras convenciones también pueden producir diferencias.
- **Independencia:** alta a nivel de organismo y metodología estadística; no se debe presumir independencia absoluta de todos los insumos subyacentes sin revisar metadatos del balance.
- **Riesgos:** confundir energía final con energía retirada en HV; no considerar pérdidas; sumar de nuevo autoconsumo o flujos locales; comparar una cifra anual con métricas horarias.
- **Clasificación:** **A únicamente para KPI anual independiente de energía**, después de conciliar conceptos y sin usar el dato como restricción de calibración si se presentará como validación.

**Uso propuesto:** integrar la potencia horaria reconstruida: (E_{modelo} = \sum_t \hat{P}_t \Delta t). Informar diferencia absoluta y relativa con 11.780,3 GWh y explicar el puente conceptual entre el límite de la curva HV y consumo final. No presentar esa diferencia como error horario del MLP.

### 3.2 Stromnetz Berlin — curvas de carga y obligación EnWG

- **Organismo:** Stromnetz Berlin GmbH, operador de la red de distribución de Berlín.
- **Acceso principal:** [Publicaciones conforme a Energiewirtschaftsgesetz (EnWG)](https://www.stromnetz.berlin/uber-uns/veroffentlichungspflichten/energiewirtschaftsgesetz-enwg/)
- **Series por nivel:** la página lista, entre otros, HV, HV–MV, MV, MV–LV y LV; publica archivos de 2023 y 2024 y un historial de curvas desde 2020. Las fichas de Berlín Open Data incluyen, por ejemplo, [historia de máximos HV](https://daten.berlin.de/datensaetze/historie-ab-2020-jahreshoechstlast-hochspannung-berlin), [historia HV–MV](https://daten.berlin.de/datensaetze/historie-ab-2020-jahreshoechstlast-hochspannung-mittelspannung-berlin) y [historia MV–LV](https://daten.berlin.de/datensaetze/historie-ab-2020-jahreshoechstlast-mittelspannung-niederspannung-berlin).
- **Base legal/resolución:** §23c(3) EnWG dispone la publicación de la carga máxima anual por nivel de red/transformación y del curso de carga como medición de potencia cuarto-horaria. [Texto legal](https://www.gesetze-im-internet.de/enwg_2005/BJNR197010005.html)
- **Cobertura:** área de red de Stromnetz Berlin. Debe comprobarse contra el perímetro administrativo 11000; no confundir área servida con límite político sin confirmarlo.
- **Resolución/unidad:** cuarto-horaria; la regulación describe *viertelstündige Leistungsmessung*. Los ficheros deben inspeccionarse para confirmar unidad, columnas, agregación y si el dato se expresa como media de potencia o energía de intervalo.
- **Período:** curvas enlazadas al menos para 2023 y 2024; históricos desde 2020 publicados por nivel.
- **Zona horaria/DST:** la página de publicación no deja inequívocamente documentada la codificación de la hora repetida/omitida de cada XLSX. Revisar encabezados y número de intervalos (año ordinario: 35.040 cuartos horarios; año bisiesto: 35.136, salvo convenciones de timestamp), preservar las etiquetas originales y documentar la conversión a UTC o a hora legal.
- **Licencia/acceso:** las fichas enlazadas de Berlin Open Data indican CC BY para determinadas series; confirmar la licencia de cada archivo específico, en especial los XLSX del año.
- **Estabilidad/reproducibilidad:** buena para cumplimiento legal, pero archivos Excel y página de publicación pueden actualizarse. Guardar descarga original, URL, fecha y huella (hash).
- **Compatibilidad:** la curva HV 2023 coincide con la familia de fuente del objetivo de entrenamiento, según el contexto del modelo. Las demás curvas son niveles o interfaces diferentes y no son automáticamente series independientes de demanda.
- **Independencia:** baja respecto del objetivo cuando el mismo operador publica las dos. Curva de año distinto sí permite holdout temporal.
- **Riesgos:** perímetro exacto; flujos hacia/desde niveles inferiores; inyecciones distribuidas; doble conteo al sumar niveles; cambio de formato o revisiones; DST.
- **Clasificación:**
  - **HV 2022 o 2024:** **B**, solo si el año no se usó para entrenar, ajustar hiperparámetros ni elegir el modelo. Evaluación fuera de muestra temporal, no independiente de operador.
  - **Niveles distintos de HV en 2023:** **C**, útiles para forma o consistencia del balance de red, después de conocer la definición exacta de cada flujo.
  - **HV 2023 ya usado como objetivo:** no es validación externa independiente; es comparación con entrenamiento.

No sumar directamente las curvas HV, HV–MV, MV, MV–LV y LV: algunas representan cargas aguas abajo o transferencias entre niveles. Hacerlo puede contar varias veces la misma energía.

### 3.3 Berlin Open Data / Energieatlas — consumo espacial de electricidad

- **Dataset:** *Energieverbrauch – Strom – [WFS]*, Senatsverwaltung für Wirtschaft, Energie und Betriebe Berlin.
- **Acceso:** [Ficha y endpoints WFS](https://daten.berlin.de/datensaetze/energieverbrauch-strom-wfs-238921d9). La ficha enlaza descripción del servicio, endpoint API y explorador WFS.
- **Cobertura:** Berlín; atributos agregados a bloques edificados, distritos administrativos y códigos postales.
- **Resolución/período:** anual, año de datos 2022; sin perfil horario.
- **Unidad/definición:** consumos eléctricos territoriales. La ficha dice que no incluyen autoconsumo ni pérdidas de red; se omite el valor de determinados bloques por protección de datos.
- **Zona horaria/DST:** no aplica a valores anuales.
- **Medición/estimación:** dataset espacial oficial; la ficha pública no explica por sí sola en detalle la cadena de medición, extrapolación o proveedor de cada segmento. Consultar los metadatos del servicio y al responsable antes de describirlo como lectura directa.
- **Licencia:** Datenlizenz Deutschland – Zero – Version 2.0 (dl-de-zero-2.0).
- **Estabilidad/reproducibilidad:** endpoint WFS reproducible, aunque puede actualizarse; archivar la respuesta, fecha, filtros y versión de metadatos.
- **Compatibilidad:** cubre el territorio ciudad, pero 2022 no coincide con año piloto. La definición excluye pérdidas y autoconsumo, por lo que difiere de una magnitud de carga HV.
- **Independencia:** incierta/parcial. El proveedor publica una fuente distinta, pero los datos de consumo podrían derivar de registros del distribuidor. No afirmar independencia de medición sin cadena de procedencia.
- **Riesgos:** celdas suprimidas; suma incompleta de bloques; diferencias de año; sesgo de selección; confundir reparto territorial anual con reparto horario; diferencias entre consumo final y medida de red.
- **Clasificación:** **C** como control espacial anual. Puede elevarse a KPI espacial A solo si la procedencia resulta independiente y el modelo no usó esas cifras para definir pesos o desagregaciones.

**Uso propuesto:** comparar participaciones (E_{distrito}/E_{Berlín}) del modelo con los agregados territoriales, dejando explícitos año, celdas ocultas y diferencias de cobertura. No presentar el resultado como validación de carga horaria por distrito.

### 3.4 50Hertz — carga de zona de control y carga vertical

- **Organismo:** 50Hertz Transmission GmbH, operador del sistema de transmisión en el norte y este de Alemania.
- **Acceso:** [Gesamtlast](https://www.50hertz.com/Transparenz/Kennzahlen/Netzdaten/Gesamtlast) y [Vertikale Netzlast](https://www.50hertz.com/de/Transparenz/Kennzahlen/Netzdaten/VertikaleNetzlast).
- **Cobertura:** Regelzone de 50Hertz, mucho mayor que Berlín; no es el código territorial 11000.
- **Definiciones:**
  - *Gesamtlast/Regelzonenlast*: carga calculada para toda la zona a partir de generación de la zona y del intercambio físico con redes vecinas.
  - *Vertikale Netzlast*: suma con signo de transferencias desde transmisión hacia redes de distribución y consumidores conectados directamente. Inyecciones de generación en media y baja tensión reducen el valor.
- **Resolución/unidad:** la carga vertical ofrece medias de cuarto de hora en MW y archivos históricos CSV anunciados en la página. La Gesamtlast histórica reciente remite a ENTSO-E.
- **Método:** magnitudes agregadas/calculadas con fuentes disponibles, no una observación de consumo de Berlín.
- **Zona horaria/DST:** confirmar convención en CSV/descarga antes de comparar; normalizar preservando las dos horas del cambio de otoño.
- **Licencia/acceso:** revisar condiciones de reutilización del archivo/página; archivar copia, URL y fecha.
- **Compatibilidad/independencia:** perímetro incompatible para KPI Berlín; operador distinto, pero agregado regional e interdependiente físicamente.
- **Riesgos:** gran diferencia de territorio; generación renovable integrada; confundir carga total con carga vertical; no poder aislar Berlín restando otros territorios sin datos compatibles.
- **Clasificación:** **C** solo para contexto, forma regional o episodios; **D** como verdad terreno de Berlín.

### 3.5 SMARD — datos de mercado de Bundesnetzagentur

- **Organismo:** Bundesnetzagentur.
- **Acceso:** [Centro de descarga SMARD](https://www.smard.de/home/downloadcenter/download-marktdaten); [definición de consumo](https://www.smard.de/page/home/wiki-article/520/2556/stromverbrauch); [uso de datos](https://www.smard.de/home/datennutzung).
- **Geografía:** Alemania o las cuatro zonas de control alemanas, incluidas las series de 50Hertz; no ofrece el municipio de Berlín como región de carga de red.
- **Resolución/unidad:** consumo realizado con medias de 15 minutos expresadas en MWh por intervalo, según el módulo. Para comparar MW medios horarios, sumar los cuatro MWh de cuarto de hora y dividir por una hora.
- **Definición:** SMARD describe el consumo como energía tomada de la red. La carga residual se calcula restando generación eólica y fotovoltaica al consumo; no equivale a demanda eléctrica.
- **Fuente/metodología:** se nutre de datos de mercado y de entregas de ENTSO-E/operadores de transmisión. SMARD y ENTSO-E no son dos mediciones independientes si la variable subyacente es la misma.
- **Zona horaria/DST:** hora legal alemana; invierno CET/MEZ = UTC+1 y verano CEST/MESZ = UTC+2. La hora de primavera falta y la hora de otoño aparece dos veces.
- **Licencia:** datos disponibles bajo CC BY 4.0; el centro permite hasta dos años por archivo según la página de descarga.
- **Estabilidad/reproducibilidad:** buen portal público; archivar selección y datos porque interfaz y datos pueden corregirse o actualizarse.
- **Clasificación:** **C** para contexto regional/nacional; **D** como validación de Berlín.

### 3.6 ENTSO-E Transparency Platform

- **Organismo:** ENTSO-E, plataforma de transparencia de operadores europeos.
- **Acceso:** [Portal de transparencia](https://transparency.entsoe.eu/); datos de carga total real se encuentran en el dominio *Load* y también alimentan publicaciones de SMARD.
- **Cobertura:** zonas de oferta/áreas reportantes nacionales o de TSO, según el producto; no es Berlín ciudad. Los datos alemanes de carga total son agregados más amplios.
- **Resolución y variable:** series de *Actual Total Load* y previsiones, generalmente cuarto-horarias u horarias según proveedor, periodo y producto. No mezclar real con forecast.
- **Zona horaria/DST:** la plataforma permite CET/CEST o UTC; para reproducibilidad solicitar/guardar UTC y hacer correspondencia explícita con Europe/Berlin.
- **Metodología/independencia:** datos reportados por TSO bajo reglas europeas; no son una medida independiente si el mismo dato reportado se vuelve a consultar a través de SMARD.
- **Acceso/licencia:** portal/API requiere credenciales para algunas rutas y está sujeto a términos de uso; guardar parámetros de consulta, fecha de extracción y versión.
- **Clasificación:** **C** para comportamiento del sistema/zona de control y comparación de contexto; **D** para validar directamente 11000.

### 3.7 Estadística industrial Berlin-Brandenburg — contraste sectorial

- **Organismo y descarga:** Amt für Statistik Berlin-Brandenburg, [reporte E IV 3-j/23 (PDF)](https://download.statistik-berlin-brandenburg.de/5cd52c3121466100/9c006ac199e8/SB_E04-03-00_2023j01_BE.pdf).
- **Cobertura y período:** establecimientos del sector manufacturero, minería y extracción en Berlín, anual 2023.
- **Dato:** consumo eléctrico reportado del sector incluido: **1.294.016 MWh**, procedente de 747 establecimientos en la tabla sectorial agregada.
- **Unidad/concepto:** electricidad consumida por establecimientos cubiertos por la encuesta, no toda la carga de la ciudad. Otra tabla distrital del informe presenta consumo energético total por combustibles, no electricidad por distrito.
- **Método/licencia:** estadística oficial; celdas pequeñas se protegen/suprimen. El reporte señala CC BY 3.0 DE.
- **Compatibilidad:** puede aportar un orden de magnitud al componente industrial; cobertura y consumo final sectorial difieren de la carga HV.
- **Clasificación:** **C** como contraste sectorial; **D** como sustituto de demanda total o como serie horaria/distrital.

### 3.8 Perfiles estándar y datasets académicos de carga regionalizada

- **Ejemplo local:** [Standardlastprofil Haushalt 2022 (Berlin Open Data)](https://daten.berlin.de/datensaetze/standardlastprofil-haushalt-2022-berlin), publicado por Stromnetz Berlin.
- **Ejemplo académico:** [Assessment of the regionalised demand response potential in Germany using an open source tool and dataset](https://arxiv.org/abs/2009.05122); modela potencial de flexibilidad de demanda regionalizada para distritos alemanes con resolución de 15 minutos, basado en perfiles, variables demográficas y tecnologías.
- **Qué representan:** perfiles típicos, cargas calculadas o potenciales regionalizados; no necesariamente energía observada de contadores para Berlín.
- **Uso posible:** contrastar la forma residencial típica o discutir decisiones de regionalización. Revisar versión, licencia y supuestos del repositorio/dataset antes de reutilizar datos.
- **Independencia:** limitada para validar un MLP con temperatura/calendario, ya que puede reutilizar supuestos o predictores semejantes.
- **Clasificación:** **D** como validación observacional independiente; a lo sumo **C** como contexto o control de supuestos, etiquetado como sintético/modelado.

## 4. Fuentes descartadas como sustitutos de Berlín

| Fuente/variable | Motivo de descarte para KPI berlinés |
|---|---|
| 50Hertz *Gesamtlast* | Carga calculada de una Regelzone extensa, no Berlín. |
| 50Hertz *Vertikale Netzlast* | Saldo vertical zonal con inyección distribuida de signo negativo; no es consumo de Berlín. |
| SMARD, región Alemania | Agregado alemán. |
| SMARD, región 50Hertz | Agregado de la zona de control, no ciudad/estado de Berlín. |
| ENTSO-E *Actual Total Load* | Perímetro de área reportante/mercado; no el municipio Berlin 11000. |
| SMARD/ENTSO-E *Residual Load* | Demanda menos generación eólica y FV, no demanda bruta/consumo de red. |
| Perfiles estándar o regionalizaciones académicas | Modelados/sintéticos; no constituyen observación independiente. |
| Estadísticas industriales anuales | Solo cubren parte del consumo y carecen de resolución horaria. |

## 5. Protocolo recomendado para la continuación del modelo

### A. Mantener una evaluación temporal ciega

1. Definir una partición por año completa. Mantener 2023 como entrenamiento/ajuste existente y reservar **2024** (o 2022) como periodo de evaluación temporal.
2. Congelar arquitectura MLP, variables, preprocesamiento, hiperparámetros y decisiones de limpieza antes de consultar métricas del año de prueba.
3. Descargar HV del año de prueba desde Stromnetz Berlin y archivar el XLSX original, fecha, URL y hash.
4. Alinear predictores horarios con timestamps inequívocos. Convertir internamente a UTC; guardar también la etiqueta de hora legal para trazabilidad. En la transición de otoño hay dos instantes distintos con la misma hora local; en primavera falta una hora.
5. Llevar la referencia cuarto-horaria a hora:
   - si son MW medios por cada cuarto: media aritmética de los cuatro intervalos para obtener MW medios horarios;
   - si son MWh de cada cuarto: sumar los cuatro valores y dividir por 1 h para MW medios horarios.
6. Informar MAE, RMSE, sesgo medio, error porcentual cuando sea estable, error en máximos, curva de duración y error energético anual. Reportar por separado invierno/verano, días laborables/festivos y hora legal.
7. Etiquetar el resultado como **validación temporal con datos del mismo operador**, no como validación externa independiente de fuente.

**Año bisiesto:** 2024 contiene 8.784 horas físicas locales/año (y más/menos registros según cómo se serialice la transición DST); 2022 y 2023 contienen 8.760 horas. Usar UTC como índice canónico evita perder o duplicar instantes físicos; no eliminar la hora repetida.

### B. KPI anual independiente de energía

1. Integrar el perfil de potencia horario del modelo como energía anual.
2. Comparar contra 11.780,3 GWh de consumo eléctrico del balance de Berlín para 2023.
3. Elaborar una tabla de conciliación: límite geográfico; nivel de tensión; pérdidas; autoconsumo/generación detrás del contador; tratamiento de bombeo/almacenamiento si aplica; energía no servida o consumos no observados; definiciones del balance.
4. Presentar el resultado como control de **magnitud anual**; no convertir el total anual en valores horarios distribuyendo por calendario y después usarlo como validación horaria.

### C. Comprobación espacial

1. Consultar el WFS del Energieatlas y registrar versión, filtros y fecha de extracción.
2. Obtener proporciones por distrito con el conjunto de distritos cubierto de forma consistente.
3. Tratar los bloques sin dato como suprimidos por privacidad, no como ceros.
4. Comparar shares distritales solo como control anual y documentar que el dato es de 2022 y excluye pérdidas y autoconsumo.
5. Confirmar procedencia del dato con la Senatsverwaltung antes de llamarlo fuente de medición independiente.

## 6. Recomendación principal y alternativa

- **Fuente principal para 2023:** balance energético anual definitivo del Amt für Statistik Berlin-Brandenburg. Es la referencia oficial más independiente y exactamente territorializada a Berlín para validar un KPI de energía anual. La transformación necesaria es integrar la potencia modelada y conciliar consumo final frente a la carga HV.
- **Alternativa para la forma horaria:** serie HV de Stromnetz Berlin en un año reservado, preferentemente 2024 para un test temporal más reciente. Agregar cuartos a horas con la regla de potencia/energía correcta y gestionar DST. Es la mejor prueba pública de generalización temporal identificada, pero sigue siendo del mismo operador.
- **Complemento espacial:** WFS del Energieatlas (2022) por distritos, como chequeo de shares territoriales con independencia no demostrada.
- **No recomendados como referencia primaria:** SMARD, ENTSO-E y 50Hertz; no tienen perímetro Berlín administrativo para la variable objetivo.

## 7. Redacción sugerida para informe CORFO

> La reconstrucción horaria se evaluó fuera de muestra frente a la curva HV publicada por Stromnetz Berlin para un año distinto del utilizado en el ajuste. Por ello, la prueba mide generalización temporal dentro de la serie del mismo operador y no constituye una validación independiente de fuente. La energía anual resultante se contrastó, además, con el balance energético oficial del Amt für Statistik Berlin-Brandenburg para Berlín, considerando que este balance representa consumo final y la curva HV un flujo de red con un límite de medición diferente. Se revisó también la distribución territorial anual disponible en el Energieatlas Berlin, cuyos datos corresponden a 2022 y no incluyen autoconsumo ni pérdidas. No se identificó una serie pública de carga horaria medida por una fuente independiente con perímetro exactamente coincidente con Berlin-administrative (11000) para 2023; por esta razón, no se reportan métricas horarias de esa fuente como validación externa independiente.

## 8. Fuentes consultadas

- [Stromnetz Berlin — publicación EnWG](https://www.stromnetz.berlin/uber-uns/veroffentlichungspflichten/energiewirtschaftsgesetz-enwg/)
- [Ley EnWG, §23c](https://www.gesetze-im-internet.de/enwg_2005/BJNR197010005.html)
- [Amt für Statistik Berlin-Brandenburg — balance energético](https://www.statistik-berlin-brandenburg.de/e-iv-4-j/)
- [Berlin Open Data — Energieverbrauch Strom WFS](https://daten.berlin.de/datensaetze/energieverbrauch-strom-wfs-238921d9)
- [50Hertz — Gesamtlast](https://www.50hertz.com/Transparenz/Kennzahlen/Netzdaten/Gesamtlast)
- [50Hertz — Vertikale Netzlast](https://www.50hertz.com/de/Transparenz/Kennzahlen/Netzdaten/VertikaleNetzlast)
- [SMARD — descargas](https://www.smard.de/home/downloadcenter/download-marktdaten)
- [SMARD — definición de consumo de red](https://www.smard.de/page/home/wiki-article/520/2556/stromverbrauch)
- [SMARD — huso y cambio horario](https://www.smard.de/home/die-zeitumstellung-auf-smard-218190)
- [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/)
- [Estadística industrial E IV 3-j/23](https://download.statistik-berlin-brandenburg.de/5cd52c3121466100/9c006ac199e8/SB_E04-03-00_2023j01_BE.pdf)
- [Berlin Open Data — perfil estándar doméstico 2022](https://daten.berlin.de/datensaetze/standardlastprofil-haushalt-2022-berlin)
- [Heitkoetter et al. — dataset regionalizado de potencial de respuesta de demanda](https://arxiv.org/abs/2009.05122)

---
**Nota de reproducibilidad:** antes de cerrar cifras comparativas en una versión técnica, descargar los XLSX/CSV originales de Stromnetz Berlin, 50Hertz o SMARD que se vayan a utilizar y verificar encabezados, unidades, huecos, revisión, huso y filas de cambio horario. La clasificación anterior se refiere a definiciones y metadatos publicados; no reemplaza esa auditoría del archivo descargado.
