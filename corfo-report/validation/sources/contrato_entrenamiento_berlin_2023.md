# Contrato de entrenamiento alemán — Berlín 2023

**Estado:** contrato provisional preparado para reentrenamiento alemán; no se han reutilizado pesos ni scaler chilenos.

El MLP chileno recibe 24 variables numéricas y una respuesta `target_scaled`. El adaptador alemán conserva los nombres y el orden para `d=8`, de modo que la arquitectura pueda reutilizarse como línea base, pero genera un scaler y pesos nuevos para Alemania. Para la ablación `d=3`/`d=5`, el mismo adaptador genera 19/21 entradas y exige construir una red con esa dimensión; no se reutilizan pesos entre dimensiones.

## Variables

| Grupo | Variables | Fuente/política | Estado |
|---|---|---|---|
| Calendario diario | `hour_sin`, `hour_cos` | Timestamp convertido a `Europe/Berlin` | Disponible |
| Calendario semanal | `dow_sin`, `dow_cos` | Lunes=0, domingo=6 | Disponible |
| Calendario anual | `doy_sin`, `doy_cos` | Año bisiesto calculado localmente | Disponible |
| Tipo de día | `is_working_day`, `is_holiday`, `is_weekend` | Feriados públicos de Berlín 2023 | Disponible, sujeto a revisión jurídica |
| Intensidad territorial | `region_comuna_share` | `1.0` para el piloto de un único territorio | **Provisional**; no equivale a fracción de Alemania |
| Shares sectoriales | `share_I`, `share_R`, `share_C`, `share_P`, `share_T` | Strombilanz anual: industria→I, hogares→R, GHD/otros→C, transporte→T, público no separable→P=0 | **Anual difundido (`annual_broadcast`)**; C/P no están separados en la fuente |
| Nivel territorial | `is_comuna` | `0` porque Berlín se trata como unidad regional/administrativa | Disponible para el piloto |
| Temperatura | `temperatura`, `temp_t - 1` … `temp_t - 7` | DWD Berlin-Tempelhof, `d=8`, `tau=1 h` | Disponible en 8.740 horas comunes |

## Resolución temporal de los shares

El piloto de Berlín se trata como una unidad regional (`is_comuna=0`). Por ello, los shares sectoriales de Strombilanz 2023 se calculan a resolución anual y se repiten para todas las horas de 2023. Esta decisión replica el flujo regional chileno; no se generan shares mensuales para el contrato de entrenamiento. La resolución queda registrada como `sector_share_temporal_resolution = annual_broadcast` en el manifiesto.

La desagregación distrital–sector se ejecuta como postproceso anual y no modifica las variables de entrada de la red neuronal.

## Objetivo y partición

La variable observada es `load_mean_MW` del perfil HV de Stromnetz Berlin, etiquetado como proxy del perímetro administrativo de Berlín. El insumo conserva la convención `timestamp_hour_end_utc`: la secuencia de 2023 termina cerrando el último intervalo en `2024-01-01T00:00:00Z`; la comprobación del período usa el año UTC y las variables de calendario usan el instante local de cierre. El objetivo se normaliza como:

```text
target_scaled = (load_mean_MW - mu_train_MW) / sigma_train_MW
```

`mu_train` y `sigma_train` se estiman solo con el primer 70 % cronológico. La partición es 70 % entrenamiento, 15 % validación y 15 % prueba; no se mezclan horas entre particiones. Esto evita que la escala use información futura.

## Brechas que deben cerrarse antes de una conclusión de factibilidad

1. Obtener una fracción territorial nacional defendible para `region_comuna_share` si se pretende transferir el modelo a Alemania completa.
2. Separar comercial y público con una fuente alemana compatible, o mantener explícitamente la agrupación GHD y evaluar sensibilidad.
3. Confirmar con Stromnetz Berlin que HV representa la carga agregada declarada y no solo clientes conectados en alta tensión.
4. Separar comercial y público o mantener explícitamente la agrupación GHD antes de declarar una desagregación sectorial definitiva. Los shares anuales ya son suficientes para el piloto regional.

## Artefactos

- Shares provisionales auditados: [`berlin_sector_shares_2023.csv`](../berlin/berlin_sector_shares_2023.csv).
- Generador: [`berlin_training_contract_2023.py`](../../prototipo_3/preprocessing/berlin_training_contract_2023.py), con `--dimension 3`, `--dimension 5` o `--dimension 8`.
- Insumo climático-demanda: [`lag_ablation_berlin_2023.md`](lag_ablation_berlin_2023.md).
- Índice versionado de los nueve Parquet: [`berlin_training_contract_2023_index.csv`](../berlin/berlin_training_contract_2023_index.csv).

El script escribe tres Parquet por dimensión fuera de Git y un manifiesto específico con hashes. La ejecución del MLP y cualquier KPI permanecen pendientes.
