# Ficha de evidencia — reconstrucción histórica de Berlín

- **ID:** `CORFO-MERLIN-EDM-DE-BERLIN-HISTORICO`.
- **Estado:** planificado; sin KPI alemán calculado.
- **País:** Alemania.
- **Territorio:** Berlín; confirmar si la referencia horaria es administrativa o del área de Stromnetz Berlin.
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
| Límites | BKG VG250 | Correspondencia territorial | Por verificar |

## Limitaciones

- Demanda de red y consumo final no son magnitudes idénticas.
- El perímetro del operador puede no coincidir con el límite administrativo.
- El consumo espacial puede excluir autoconsumo, pérdidas o registros suprimidos.
- Los sectores alemanes no necesariamente replican los cinco sectores chilenos.
- El horario alemán contiene intervalos locales ausentes o repetidos.

No se declara cumplimiento hasta completar la auditoría, ejecutar el modelo y generar los artefactos definidos en [`kpi_plan.md`](kpi_plan.md).
