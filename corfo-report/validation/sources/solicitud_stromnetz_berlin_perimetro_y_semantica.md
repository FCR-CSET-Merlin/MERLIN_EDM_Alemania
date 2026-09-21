# Solicitud preparada a Stromnetz Berlin — perímetro y semántica HV

**Estado:** preparada para envío; no enviada desde este repositorio.  
**Canal sugerido:** formulario o contacto de [Stromnetz Berlin](https://www.stromnetz.berlin/kontakt/).  
**Objetivo:** obtener una respuesta citable para cerrar la Fase 0 y validar el contrato de datos.

## Preguntas que deben responderse

1. ¿El archivo `Jahreshöchstlast der Netzlast – Lastverlauf Hochspannung` representa la carga agregada medida en la frontera HV, incluyendo la entrega a las redes de media y baja tensión, o solamente los clientes conectados directamente a 110 kV?
2. ¿La columna `Wert` es un promedio de potencia activa en kW para cada cuarto de hora? ¿El timestamp `Datum/Zeit` representa el inicio o el fin del intervalo?
3. ¿Cómo deben interpretarse los intervalos repetidos y ausentes en `Europe/Berlin` durante el cambio CET/CEST? ¿Existe una versión con timestamp UTC o con indicador de `fold`?
4. ¿El campo `Arbeit in kWh` es exactamente la suma de `Wert × 0,25 h`? ¿Qué tratamiento se aplica a redondeos, pérdidas, consumo operativo, generación distribuida y flujos inversos?
5. ¿Qué polígono, lista de municipios o archivo GIS corresponde a `Geografische Fläche des Netzgebietes` (1.046,64 km²) y cuál corresponde a `Versorgte Fläche Hochspannung und Mittelspannung` (891,12 km²)?
6. ¿Los perfiles HV 2019–2023 comparten el mismo perímetro y metodología? En particular, ¿pueden confirmar las anomalías de timestamps observadas en 2020–2022?

## Borrador en alemán

**Betreff:** Bitte um fachliche Klärung der HV-Lastgänge 2019–2023 und der Netzgebietsgrenzen

Sehr geehrte Damen und Herren,

wir arbeiten an einer historischen Rekonstruktion der elektrischen Nachfrage für Berlin und verwenden ausschließlich die von Stromnetz Berlin gemäß § 23c EnWG veröffentlichten Daten. Für die fachlich korrekte und reproduzierbare Nutzung der Dateien `Jahreshöchstlast der Netzlast – Lastverlauf Hochspannung` 2019–2023 bitten wir um eine kurze schriftliche Klärung der folgenden Punkte:

1. Bezieht sich der HV-Lastgang auf die gesamte über die Hochspannungsebene übertragene Netzlast einschließlich der Abgabe an nachgelagerte Netz- und Umspannebenen, oder ausschließlich auf unmittelbar in Hochspannung angeschlossene Entnahmestellen?
2. Sind die Werte `Wert` arithmetische Mittelwerte der Wirkleistung in kW je 15-Minuten-Intervall? Bezeichnet `Datum/Zeit` den Beginn oder das Ende des Intervalls?
3. Wie sollen die wiederholten bzw. fehlenden Viertelstunden bei der Umstellung zwischen MEZ und MESZ behandelt werden? Gibt es eine UTC-Zeit oder einen Kennzeichner für die wiederholte Stunde?
4. Entspricht `Arbeit in kWh` exakt der Summe der Viertelstundenwerte × 0,25 h? Wie werden Rundungen, Netzverluste, Betriebsverbrauch, dezentrale Einspeisung und Rückspeisungen behandelt?
5. Können Sie uns die Geometrie oder eine kommunale Zuordnung für `Geografische Fläche des Netzgebietes` (1.046,64 km²) und für die versorgte Fläche Hochspannung/Mittelspannung (891,12 km²) bereitstellen?
6. Gelten für die HV-Lastgänge 2019–2023 derselbe geografische Perimeter und dieselbe Methodik? Können Sie insbesondere die auffälligen Datumsfolgen in den Dateien 2020–2022 bestätigen oder korrigieren?

Wir würden die Antwort mit Quellenangabe, Version und Abrufdatum in der technischen Dokumentation eines öffentlich geförderten Forschungsprojekts zitieren. Eine kurze Bestätigung oder ein Verweis auf die zuständige Veröffentlichung würde uns bereits helfen.

Vielen Dank im Voraus.

Mit freundlichen Grüßen

[Nombre / institución / proyecto]
