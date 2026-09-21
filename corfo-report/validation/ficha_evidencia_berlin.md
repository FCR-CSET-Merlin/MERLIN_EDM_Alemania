# Ficha de evidencia — reconstrucción histórica de Berlín

- **ID:** `CORFO-MERLIN-EDM-DE-BERLIN-HISTORICO`.
- **Estado:** planificado; sin KPI alemán calculado.
- **País:** Alemania.
- **Territorio:** `Berlin-administrative` (`ars/ags=11000`, geometría BKG VG250); la serie Stromnetz Berlin se reportará como `Stromnetz-Berlin-HV-area-proxy` hasta confirmar equivalencia geométrica.
- **Objetivo:** reconstrucción horaria y validación anual/sectorial.
- **Fecha de corte, commit y entorno:** pendientes.
- **Responsable y revisor:** pendientes.

## Fuentes previstas

| Insumo | Fuente | Función | Estado |
|---|---|---|---|
| Demanda horaria | Stromnetz Berlin | Objetivo horario candidato | Por verificar |
| Balance anual | Statistik Berlin-Brandenburg | Referencia total/sectorial | Por verificar |
| Distribución espacial | Umweltatlas Berlin | Validación distrital | Por verificar |
| Temperatura | DWD o ERA5-Land | Variable explicativa | Por verificar |
| Límites | BKG VG250 | Perímetro administrativo reproducible de Berlín (`11000`) | Aceptado para el piloto; correspondencia exacta con red pendiente |

## Limitaciones

- Demanda de red y consumo final no son magnitudes idénticas.
- El perímetro publicado por el operador contiene dos métricas no reconciliadas públicamente: 891,12 km² y 1.046,64 km².
- La serie HV se usa como proxy del territorio administrativo; no se afirma que su polígono sea idéntico al BKG.
- El consumo espacial puede excluir autoconsumo, pérdidas o registros suprimidos.
- Los sectores alemanes no necesariamente replican los cinco sectores chilenos.
- El horario alemán contiene intervalos locales ausentes o repetidos.

No se declara cumplimiento hasta completar la auditoría, ejecutar el modelo y generar los artefactos definidos en [`kpi_plan.md`](kpi_plan.md).
