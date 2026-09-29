# Ficha de evidencia — reconstrucción histórica de Berlín

- **ID:** `CORFO-MERLIN-EDM-DE-BERLIN-HISTORICO`.
- **Estado:** Fase 4 cerrada con limitación documentada; KPI interno 2023 y holdout temporal 2024 cumplen MAPE <=35 %; KPI horario independiente y espacial independiente no evaluables.
- **País:** Alemania.
- **Territorio:** `Berlin-administrative` (`ars/ags=11000`, geometría BKG VG250); la serie Stromnetz Berlin se reportará como `Stromnetz-Berlin-HV-area-proxy` hasta confirmar equivalencia geométrica.
- **Objetivo:** reconstrucción horaria y validación anual/sectorial.
- **Fecha de corte:** 29 de septiembre de 2026.
- **Commit y entorno de entrenamiento:** corrida reproducible con Python 3.13.13, TensorFlow 2.21.0, NumPy 2.5.3 y semilla 2023; commit se registra al publicar los artefactos.
- **Responsable y revisor:** pendientes.

## Fuentes previstas

| Insumo | Fuente | Función | Estado |
|---|---|---|---|
| Demanda horaria | Stromnetz Berlin HV 2019–2023 | Objetivo horario de red y proxy territorial | GO condicionado; semántica general confirmada, alcance HV/timestamps pendientes |
| Balance anual | Statistik Berlin-Brandenburg, edición corregida 2023 | Referencia total/sectorial | Auditada; consistencia anual condicionada |
| Distribución espacial | Umweltatlas Berlin WFS, campo `j2023g` | Validación distrital | Auditada; salida distrital del modelo pendiente |
| Temperatura | DWD Berlin-Tempelhof 00433 | Variable explicativa horaria | Seleccionada condicionada; 5 faltantes 2023 y representatividad espacial pendientes |
| Límites | BKG VG250 | Perímetro administrativo reproducible de Berlín (`11000`) | Aceptado para el piloto; correspondencia exacta con red pendiente |

## Capas de validación

La validación se ejecutará según el [contrato de validación](sources/contrato_validacion_berlin.md):

- capa A: MAPE horario interno sobre el tramo HV reservado;
- capa B: consistencia anual condicionada con la Strombilanz;
- capa C: consistencia espacial con Umweltatlas;
- capa D: control de forma agregado con SMARD, sin validez de KPI Berlín;
- capa E: comparador horario independiente de Berlín, todavía no disponible.

La matriz de fuentes y la plantilla de resultados están en
[`sources/comparaciones_externas_berlin.csv`](sources/comparaciones_externas_berlin.csv)
y [`berlin/comparaciones_externas_2023.csv`](berlin/comparaciones_externas_2023.csv).

## Resultado de la homologación externa 2023

La auditoría reproducible está en
[`berlin/external_2023/auditoria_homologacion_externa_berlin_2023.md`](berlin/external_2023/auditoria_homologacion_externa_berlin_2023.md).
Con la serie HV observada se obtuvo:

- HV anual: `11.812,177946 GWh`;
- Strombilanz, consumo final: `11.780,229 GWh`; diferencia relativa `+0,271208 %`;
- Umweltatlas, suma de 12 distritos `j2023g`: `11.899,370 GWh`; diferencia HV–WFS `-0,732745 %`.

Estos valores son controles de consistencia. La inferencia d=3 exportada suma 11.738,063 GWh en las 8.740 filas completas (brecha -1,355596 % frente a la suma distrital `j2023g`). La salida distrital usa los shares `j2023g` como pesos fijos; por eso la coincidencia de shares es una consistencia condicionada y no una validación espacial independiente.

## Cierre de validación

- Test interno 2023: MAPE 5,089161454 % sobre 1.311 horas.
- Holdout temporal 2024: MAPE 3,095865639 % sobre 8.776 horas válidas de 8.784.
- Control anual 2023 modelo–Strombilanz: −0,357941 %, condicionado por shares de entrada y cobertura parcial.
- No se identificó una referencia horaria pública independiente compatible con el perímetro 11000.

## Limitaciones

- Demanda de red y consumo final no son magnitudes idénticas.
- El perímetro publicado por el operador contiene dos métricas no reconciliadas públicamente: 891,12 km² y 1.046,64 km².
- La serie HV se usa como proxy del territorio administrativo; no se afirma que su polígono sea idéntico al BKG.
- El consumo espacial puede excluir autoconsumo, pérdidas o registros suprimidos.
- Los sectores alemanes no necesariamente replican los cinco sectores chilenos.
- El horario alemán contiene intervalos locales ausentes o repetidos.
- Los CSV HV 2020–2022 contienen saltos o etiquetas de fecha que requieren normalización y confirmación del operador.
- La Strombilanz es consumo final anual y no reemplaza la referencia horaria de red.
- La tabla HV–temperatura contiene 20 filas sin ocho valores climáticos válidos; no se imputaron. La inferencia se exportó sobre 8.740 filas completas.
- La desagregación distrital conserva la forma horaria agregada y usa shares anuales fijos; no acredita que la red haya aprendido perfiles horarios diferenciados por distrito.

El KPI horario interno del piloto está documentado en [`berlin/kpi_validation.csv`](berlin/kpi_validation.csv) y cumple el umbral de 35 %. El cumplimiento externo horario y el KPI espacial independiente siguen pendientes.
