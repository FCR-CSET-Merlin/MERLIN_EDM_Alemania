# Series horarias — Berlín, Alemania

Las series horarias o de 15 minutos pueden ser pesadas y no se versionan directamente en Git. Cada entrega deja un índice con nombre, período, número de filas, unidad, zona horaria, fuente, ubicación externa y SHA-256.

La primera entrega reproducible está disponible en [`berlin_inputs_2023_index.csv`](berlin_inputs_2023_index.csv). Los archivos pesados se generan bajo `prototipo_3/data/de_alemania/` y permanecen ignorados por Git.

## Entregas 2023

- HV 15-min normalizada: 35.040 filas, índice UTC generado por secuencia, marcas publicadas conservadas.
- HV horaria: 8.760 filas, media de potencia (`load_mean_MW`) y energía (`energy_MWh`).
- Temperatura DWD Berlin-Tempelhof: 8.760 horas; 5 faltantes explícitos, sin imputación.
- Tabla integrada HV–temperatura: 8.760 filas; 8.740 completas para temperatura contemporánea y siete rezagos.

La tabla integrada aún requiere resolver shares sectoriales, calendario alemán y la semántica definitiva de los timestamps HV antes de entrenar la red.
