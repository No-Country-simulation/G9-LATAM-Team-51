# Definición reproducible de categorías de eficiencia energética

> **Estado:** especificación autocontenida de `ideal-relative-v1`.
> **Entradas de datos:** `household_sensors.zip` e `ideal_metadata_and_surveys.zip`, ambos originales del dataset IDEAL.
> **Unidad de análisis:** un hogar durante un mes calendario (`hogar-mes`).

## 1. Objetivo y alcance

El objetivo es construir, a partir de lecturas eléctricas de IDEAL, una etiqueta de tres clases:

- `Eficiente`
- `Moderado`
- `Ineficiente`

La etiqueta se obtiene con una regla relativa y reproducible. IDEAL no contiene una etiqueta observada de eficiencia, por lo que estas clases son **pseudoetiquetas**: describen la posición de cada hogar-mes dentro de la población de entrenamiento y no una certificación energética oficial.

La metodología admite dos modos de ejecución equivalentes: uno secuencial y didáctico, que expone cada resultado intermedio, y otro paralelo, que distribuye hogares entre procesos para reducir el tiempo total. La paralelización solo cambia el orden y la velocidad con que se agregan hogares; antes del split y de la escritura, las filas se ordenan por `(homeid, year_month)`. Ambos modos aplican las mismas constantes, validaciones, fórmulas, semilla y columnas. Por ello deben producir exactamente las mismas filas, splits, referencias, umbrales, scores y categorías; únicamente la telemetría de duración puede variar. Una diferencia metodológica o en los datos resultantes se considera un error de implementación, no una variación aceptable.

El proceso completo es:

```text
household_sensors.zip                ideal_metadata_and_surveys.zip
lecturas de red a 1 Hz               home.csv + appliance.csv
             │                                  │
             └──────────────┬───────────────────┘
                            ▼
              cruce reproducible por homeid
                            │
                            ▼
               agregación hogar-mes y calidad
                            │
                            ▼
           split por hogar, estratificado por tipo
                            │
                            ▼
       percentiles y terciles ajustados solo con train
                            │
                            ▼
           dataset etiquetado + metadatos reproducibles
```

## 2. Advertencia de uso

> Las categorías representan perfiles relativos dentro de una muestra de viviendas de Edimburgo, Reino Unido. No son equivalentes a ratings oficiales A–G, no permiten afirmar causalidad, no deben usarse para facturación y no son directamente generalizables a viviendas latinoamericanas. Cualquier uso real requiere validación externa con una población representativa y, de ser posible, una etiqueta de eficiencia observada.

## 3. Entradas originales y descubrimiento del universo

### 3.1 `household_sensors.zip`

De este ZIP se utilizan los miembros que cumplen el patrón:

```text
sensordata/home<id>_*_electric-mains_electric-combined.csv.gz
```

Cada miembro corresponde al consumo eléctrico general de una vivienda y contiene filas con esta forma:

```text
timestamp_utc,potencia_watts
```

Las lecturas se procesan en streaming. No se extrae el ZIP completo y no se carga un hogar completo en memoria.

### 3.2 `ideal_metadata_and_surveys.zip`

Los streams eléctricos no contienen el tipo de vivienda ni el inventario de equipos. Se utilizan únicamente dos archivos originales dentro del ZIP de metadata:

- `metadata/home.csv`: relación `homeid → hometype`;
- `metadata/appliance.csv`: inventario de appliances declarados por hogar.

El tipo se transforma así:

```text
flat                → Departamento
house_or_bungalow   → Casa
```

La cantidad de equipos se calcula por hogar como:

```text
cantidad_equipos = Σ number
                    para filas con powertype == "electric"
```

Se suma `number`, no simplemente la cantidad de filas, porque una fila puede representar varias unidades del mismo tipo de appliance.

### 3.3 Manifiesto reproducible

El manifiesto no está escrito manualmente. En cada ejecución se descubren los medidores generales del ZIP de sensores y se cruzan por `homeid` con ambos archivos de metadata. El proceso se detiene si un medidor descubierto carece de tipo de inmueble o de al menos un equipo eléctrico declarado.

Con los archivos originales utilizados se descubren 254 viviendas con medidor general, todas con metadata completa:

| Tipo | Viviendas descubiertas |
| --- | --- |
| Departamento | 144 |
| Casa | 110 |
| **Total** | **254** |

## 4. Limpieza de lecturas crudas

Para cada stream se aplican estas reglas antes de agregar:

1. Interpretar el timestamp como UTC y convertirlo a `Europe/London` cuando se necesite hora local.
2. Descartar filas con timestamp inválido, valor no numérico, `NaN`, infinito o potencia negativa.
3. Descartar potencias superiores a 30.000 W como valores físicamente implausibles para este contexto residencial.
4. Conservar la primera lectura cuando dos timestamps iguales son adyacentes y descartar la siguiente como duplicado.
5. Descartar cualquier timestamp menor que el anterior. Una repetición no adyacente también cae en esta regla y queda registrada como lectura fuera de orden.
6. Excluir el intervalo defectuoso documentado oficialmente en IDEAL
   (`ideal_documentation.zip → documentation/IDEALdata.md`, línea 365,
   sección "Known issues"). Cita literal:

   > All sensor data in the hour between 08:50 and 09:50 on 17th April 2018
   > should be considered unreliable. Due to a server error, too many data
   > points are recorded during this time.

   Frontera final abierta:

```text
   2018-04-17 08:50:00 UTC ≤ timestamp < 2018-04-17 09:50:00 UTC
```

   La exclusión se aplica **antes** de acumular consumo, coberturas y horas.
   `build_label.py` asume que el dataset mensual ya llega corregido; no
   puede eliminar la hora defectuosa después de que se agregó al mes.

Cada lectura válida de potencia se convierte a energía mediante:

```text
energía_kWh = potencia_watts × segundos_observados / 3.600.000
```

Como la frecuencia esperada es una lectura por segundo, la suma mensual es:

```text
observed_kwh = Σ potencia_watts / 3.600.000
```

## 5. Construcción de la observación hogar-mes

### 5.1 Cobertura total

El número esperado de segundos se calcula entre el inicio y fin del mes en `Europe/London`, convertido a UTC. Esto incorpora correctamente los cambios de horario de verano.

```text
month_coverage = valid_seconds / expected_seconds
consumo_kwh = observed_kwh / month_coverage
```

`consumo_kwh` es el consumo mensual ajustado por cobertura. No se suman consumos diarios ya ajustados; primero se suman los componentes observados y luego se ajusta una sola vez al nivel mensual.

### 5.2 Cobertura y energía de horario pico

El horario pico se define en hora local de Londres:

```text
17:00 ≤ hora local < 21:00
```

Para cada mes:

```text
peak_coverage = peak_valid_seconds / peak_expected_seconds
adjusted_peak_kwh = observed_peak_kwh / peak_coverage
peak_energy_share = adjusted_peak_kwh / consumo_kwh
uso_horario_pico = peak_energy_share > 0,25
```

La cobertura pico se calcula por separado de la cobertura total. No se aplica el mismo factor de ajuste al numerador y al denominador.

### 5.3 Horas de alto consumo

Una hora UTC es evaluable cuando tiene al menos 90% de sus segundos esperados. Su consumo ajustado es:

```text
hour_coverage = valid_seconds_hour / 3.600
adjusted_hour_kwh = observed_hour_kwh / hour_coverage
```

Se considera hora de alto consumo cuando:

```text
adjusted_hour_kwh > 0,5 kWh
```

Cada hora UTC se asigna a su fecha local. Un día local es utilizable cuando al menos 90% de sus 23, 24 o 25 horas esperadas es evaluable. Para cada día utilizable:

```text
day_coverage = evaluable_hours / expected_hours
adjusted_high_hours_day = min(high_evaluable_hours / day_coverage, expected_hours)
```

Finalmente:

```text
average_daily_high_hours = promedio(adjusted_high_hours_day)
horas_alto_consumo = min(24, floor(average_daily_high_hours + 0,5))
complete_day_ratio = usable_days / calendar_days
```

### 5.4 Cinco variables de clasificación

| Variable | Tipo y dominio | Definición |
| --- | --- | --- |
| `consumo_kwh` | float > 0 | Consumo mensual ajustado por cobertura. |
| `uso_horario_pico` | boolean | `peak_energy_share > 0,25`. |
| `cantidad_equipos` | entero ≥ 1 | Suma de equipos eléctricos declarados en `metadata/appliance.csv`; constante dentro del hogar. |
| `tipo_inmueble` | `Casa` o `Departamento` | Transformación de `hometype` en `metadata/home.csv`; constante dentro del hogar. |
| `horas_alto_consumo` | entero entre 0 y 24 | Promedio diario ajustado, redondeado al entero más cercano. |

### 5.5 Variables descriptivas de auditoría

Estas variables **no alimentan** el score ni las categorías; viven en un
sidecar `ideal_monthly_audit.parquet` unido 1:1 por `(homeid, year_month)`
con el dataset canónico `ideal_monthly_features_labeled.parquet`.

No participan en: elegibilidad; `FEATURE_COLUMNS`; split; percentiles;
score; terciles; categoría.

#### Potencia promedio

```text
potencia_promedio_w = sum_watts / valid_seconds
```

Donde `valid_seconds` representa muestras aceptadas bajo la frecuencia
esperada de 1 Hz. La potencia promedio se deriva de las lecturas aceptadas,
no de `peak_energy_share` ni de `observed_kwh`.

#### Potencia máxima

```text
potencia_maxima_w = máximo de watts aceptados en el hogar-mes
```

Se calcula después de descartar timestamps inválidos, valores no numéricos
o no finitos, potencia negativa, potencia superior a 30.000 W, timestamps
duplicados o desordenados, y el intervalo defectuoso del 17 de abril de
2018 documentado por IDEAL. La potencia máxima tampoco se puede reconstruir
desde `observed_kwh` o `peak_energy_share`.

#### Consumo nocturno

Ventana nocturna fuzzy en hora local:

```text
hora_local >= 22:00  o  hora_local < 06:00
```

Fronteras exactas:

```text
[22:00, 24:00) ∪ [00:00, 06:00)
```

Cálculos:

```text
observed_night_kwh = night_sum_watts / 3.600.000
night_coverage = night_valid_seconds / night_expected_seconds

si night_coverage >= 0,90:
    consumo_nocturno_kwh = observed_night_kwh / night_coverage
    night_eligible = true
si no:
    consumo_nocturno_kwh = null
    night_eligible = false
```

Los segundos esperados se calculan convirtiendo a UTC los límites locales
de cada intervalo nocturno. Así, las noches asociadas al cambio DST pueden
tener 7, 8 u 9 horas reales (25.200, 28.800 o 32.400 segundos).

#### `audit_schema_version`

```text
audit_schema_version = "ideal-audit-v1"
```

Indica que el sidecar está versionado de forma independiente del
`category_method_version` del score.

## 6. Elegibilidad por calidad

Una fila hogar-mes es elegible solo si cumple simultáneamente:

```text
month_coverage      ≥ 0,90
peak_coverage       ≥ 0,90
complete_day_ratio  ≥ 0,80
0 ≤ peak_energy_share ≤ 1
consumo_kwh > 0
```

El 90% es el umbral principal: conserva suficientes hogares para el entrenamiento sin aceptar meses con grandes vacíos de medición. El consumo y la energía pico se corrigen por sus coberturas respectivas, y la condición de días completos aporta un segundo control independiente. Estos umbrales son decisiones de preparación de datos, no propiedades aprendidas por el modelo.

Como análisis de sensibilidad se vuelve a contar el dataset con umbrales de cobertura mensual y pico más estrictos, sin modificar el corte de días completos:

| Umbral mensual y pico | Filas hogar-mes | Hogares |
| --- | --- | --- |
| 0,90 | 555 | 151 |
| 0,92 | 480 | 137 |
| 0,93 | 437 | 126 |
| 0,94 | 370 | 107 |
| 0,95 | 300 | 93 |

El resultado demuestra que el volumen de 555 filas depende explícitamente de usar 0,90. No debe presentarse como si el cambio de volumen fuera independiente del criterio de cobertura.

No se eliminan automáticamente consumos bajos: pueden corresponder a una vivienda eficiente, desocupada o de uso estacional. Sin información observada de ocupación, excluirlos censuraría la cola baja de la distribución.

## 7. Separación train/test sin leakage

La partición se hace sobre una tabla con una fila por hogar, ordenada primero por `homeid`:

```text
(homeid, tipo_inmueble)
```

Se usa `train_test_split` con:

```text
test_size = 0,25
random_state = 42
stratify = tipo_inmueble
```

Después, todas las filas mensuales de un hogar se asignan al mismo split. Esto evita que meses autocorrelacionados de una misma vivienda aparezcan simultáneamente en train y test.

La ordenación previa es parte de la especificación. `train_test_split` usa posiciones de entrada; sin un orden estable, el mismo `random_state` podría elegir hogares diferentes si cambia el orden de lectura de los archivos.

Controles obligatorios:

- ningún `homeid` puede aparecer en ambos splits;
- cada tipo debe tener al menos dos hogares antes del split;
- cada tipo presente en test debe tener referencia en train;
- no puede haber duplicados de `(homeid, year_month)`;
- `tipo_inmueble` y `cantidad_equipos` deben ser constantes dentro de cada hogar.

## 8. Percentiles ajustados solo con train

Para un valor `x` y una referencia ordenada de train:

```text
percentil(x; ref_train) =
    [cantidad(ref < x) + 0,5 × cantidad(ref == x)]
    / cantidad(ref)
```

Se construyen dos referencias separadas por `tipo_inmueble`:

- `percentile_consumo`: referencia de todas las filas hogar-mes de train del mismo tipo.
- `percentile_equipos`: referencia de hogares únicos de train del mismo tipo. Un hogar no gana más peso por tener más meses.

Las referencias se congelan y se aplican sin recalcular a train y test. Un valor inferior a toda la referencia obtiene 0; uno superior a toda la referencia obtiene 1.

## 9. Score `ideal-relative-v1`

```text
score =
    0,60 × percentile_consumo
  + 0,20 × peak_component
  + 0,15 × high_hours_component
  + 0,05 × percentile_equipos
```

Donde:

```text
peak_component = 1 si uso_horario_pico es True; 0 en caso contrario
high_hours_component = min(horas_alto_consumo / 12, 1)
```

Justificación de pesos:

| Componente | Peso | Justificación |
| --- | --- | --- |
| Consumo relativo dentro del tipo | 60% | Es la señal principal de uso energético mensual. |
| Uso en horario pico | 20% | Captura concentración del consumo en una ventana operativamente relevante. |
| Horas de alto consumo | 15% | Distingue consumo sostenido de picos breves. |
| Equipos relativos dentro del tipo | 5% | Se conserva como señal débil; más equipos no implica necesariamente ineficiencia. |

No se divide consumo por cantidad de equipos. Ese cociente puede premiar artificialmente a una vivienda por declarar más equipos aun cuando mantenga el mismo consumo.

El resultado está acotado a `[0, 1]`.

## 10. Conversión del score a categorías

Los cortes se ajustan exclusivamente con scores de train:

```text
t1 = percentil lineal 33,333... de score_train
t2 = percentil lineal 66,666... de score_train

score < t1       → Eficiente
t1 ≤ score ≤ t2  → Moderado
score > t2       → Ineficiente
```

Las fronteras exactas pertenecen a `Moderado`. Si `t1 >= t2` o train no contiene las tres clases, el proceso se detiene: no se introducen jitter, identificadores ni cortes manuales para fabricar clases.

El método de interpolación del percentil es `linear`; se declara explícitamente para evitar que un cambio de valor por defecto entre versiones altere los cortes.

Usar terciles de train evita calibrar cortes con información de test. Los terciles equilibran aproximadamente train por construcción, pero ese balance no demuestra validez científica.

## 11. Diagnósticos reproducibles

Los diagnósticos no modifican filas, scores ni etiquetas. Se calculan antes de guardar los metadatos.

### 11.1 Estabilidad temporal

Para hogares con al menos tres meses se consideran solamente pares de meses calendario consecutivos. Se registra:

- mediana de transiciones por hogar;
- proporción con dos o más transiciones;
- proporción con salto directo `Eficiente ↔ Ineficiente`;
- `temporal_stability_low_power = true` si hay menos de 30 hogares evaluables;
- warning si más de 25% tiene dos o más transiciones o más de 10% presenta un salto extremo.

### 11.2 Balance por tipo

Se calcula la tabla `tipo_inmueble × categoria`. Se registra un warning si alguna categoría representa menos de 10% de las filas de un tipo.

### 11.3 Coherencia descriptiva

Se calcula Spearman entre la categoría ordinal (`0, 1, 2`) y:

- `peak_energy_share` continuo;
- `month_coverage`;
- `cantidad_equipos`.

La última relación es parcialmente circular porque equipos aporta 5% al score. Ninguna de estas correlaciones es validación externa.

### 11.4 Sensibilidad al ajuste por cobertura

```text
diff = corr_spearman(categoria, consumo_kwh)
     - corr_spearman(categoria, observed_kwh)
```

- `|diff| < 0,05`: ajuste prácticamente neutro.
- `|diff| > 0,15`: warning para inspección.

Como ambas variables comparten la misma energía observada, este diagnóstico no permite atribuir causalidad.

## 12. Artefactos generados

La ejecución produce cinco artefactos en el directorio configurado de
salida. Ninguno de ellos se utiliza como entrada para construir los otros:
todos se derivan en una misma ejecución desde los dos ZIP originales.

1. `ideal_monthly_features.csv`: filas hogar-mes elegibles antes de etiquetar.
2. `ideal_monthly_features_labeled.csv`: dataset con split, percentiles,
   componentes, score y categoría (formato CSV, auditable).
3. `ideal_monthly_features_labeled.parquet`: idem en formato parquet
   (preserva tipos numéricos y booleans sin artefactos de texto).
4. `ideal_monthly_audit.parquet`: sidecar con las variables descriptivas de
   auditoría (potencia promedio, máxima, consumo nocturno) unido 1:1 por
   `(homeid, year_month)` con el dataset canónico etiquetado. No alimenta
   score, categoría ni elegibilidad.
5. `label_metadata.json`: configuración, manifiesto descubierto, referencias
   de train, terciles, conteos de limpieza, sensibilidad de cobertura,
   diagnósticos, hashes de insumos y scripts, `run_id`, `audit_schema`.

El dataset etiquetado (CSV y parquet) incluye como columnas constantes:

```text
category_method_version = "ideal-relative-v1"
sample_flag = true | false
```

El sidecar de auditoría incluye como columna constante:

```text
audit_schema_version = "ideal-audit-v1"
```

Los metadatos también incluyen `run_id` (ISO 8601 UTC), `input_hashes`
(SHA-256 de `household_sensors.zip` e `ideal_metadata_and_surveys.zip`),
`script_hashes` (SHA-256 de los dos scripts fuente) y la sección
`audit_sidecar` con la ruta y contracto del sidecar. Así, las etiquetas
pueden auditarse sin recalcular referencias usando test.

El entorno de referencia utilizado para validar los resultados fue:

```text
Python          3.10.0
numpy           2.2.6
pandas          2.3.3
scipy           1.15.3
scikit-learn    1.7.2
pyarrow         (requerido para parquet)
matplotlib      (requerido para EDA)
jupytext        1.19.4  (solo para convertir el script a .ipynb)
```

## 13. Resultado reproducible de referencia

Con los dos ZIP originales y la configuración de esta especificación se obtiene:

| Etapa | Viviendas | Filas hogar-mes |
| --- | --- | --- |
| Medidores generales descubiertos | 254 | — |
| Meses examinados antes de elegibilidad | 254 | 2.622 |
| Dataset elegible | 151 | 555 |
| Train | 113 | 431 |
| Test | 38 | 124 |

El dataset elegible contiene 84 Departamentos y 67 Casas. El split reproducible queda distribuido así:

| Split | Departamentos | Casas |
| --- | --- | --- |
| Train | 63 hogares / 248 filas | 50 hogares / 183 filas |
| Test | 21 hogares / 70 filas | 17 hogares / 54 filas |

Los terciles ajustados exclusivamente con las 431 filas de train son:

```text
t1 = 0,3629506154
t2 = 0,6111345793
```

Distribución resultante:

| Split | Eficiente | Moderado | Ineficiente |
| --- | --- | --- | --- |
| Train | 144 | 143 | 144 |
| Test | 53 | 38 | 33 |

`sample_flag = false` porque train contiene al menos 30 hogares de cada tipo. Esto solo indica que se supera el umbral operativo definido; no demuestra representatividad geográfica ni validez externa.

## 14. Límites de esta entrega y contrato del dataset

Esta entrega cubre exclusivamente la preparación del dataset canónico,
la definición de las pseudoetiquetas y el EDA. Quedan **fuera de alcance**:

- entrenamiento de modelos;
- evaluación con métricas (accuracy, F1, matriz de confusión);
- serialización de modelos (`.joblib`, `.pkl`, `.onnx`);
- API REST;
- integración con OCI;
- frontend.

**Contrato del dataset entregado:**

| Artefacto | Filas | Columnas | Uso |
| --- | --- | --- | --- |
| `ideal_monthly_features.csv` | 555 | 13 | Filas hogar-mes elegibles, sin etiquetar |
| `ideal_monthly_features_labeled.csv` | 555 | 22 | Canónico: 5 features + score + categoria + split + auditoría |
| `ideal_monthly_features_labeled.parquet` | 555 | 22 | Idem en parquet (preserva tipos) |
| `ideal_monthly_audit.parquet` | 555 | 11 | Sidecar: potencia promedio, máxima, consumo nocturno |
| `label_metadata.json` | — | — | Referencias congeladas, terciles, diagnósticos, audit_schema |

**Reglas de uso para el equipo de Data Science (entrenamiento delegado):**

- Las 5 variables canónicas son los únicos predictores: `consumo_kwh,
  uso_horario_pico, cantidad_equipos, tipo_inmueble, horas_alto_consumo`.
- No usar como predictores: `homeid`, `year_month`, `month_coverage`,
  `peak_coverage`, `peak_energy_share`, `complete_day_ratio`,
  `observed_kwh`, `source_member`, columnas de auditoría.
- `homeid` debe usarse como grupo en `GroupKFold` o `StratifiedGroupKFold`
  para que todos los meses de una vivienda queden en el mismo fold.
- En inferencia: **no** recalcular percentiles ni terciles por solicitud.
  Aplicar el preprocesador y clasificador entrenados.
- Las referencias congeladas en `label_metadata.json` existen para
  auditoría de las pseudoetiquetas, no como segunda regla de inferencia.

## 15. Limitaciones

- Aunque se descubren los 254 medidores generales, los controles de calidad dejan 151 hogares con al menos un mes elegible.
- `sample_flag = false` no convierte estos datos en una muestra representativa de otros países, climas o poblaciones.
- IDEAL corresponde a Edimburgo entre 2016 y 2018; clima, tarifas y hábitos difieren de otros lugares.
- La etiqueta es construida a partir de las mismas variables que recibirá el clasificador.
- `uso_horario_pico` pierde magnitud al ser booleano.
- El umbral de 0,5 kWh por hora es absoluto y puede penalizar viviendas grandes.
- `cantidad_equipos` no captura ocupación, superficie, eficiencia del aparato ni intensidad de uso.
- Los meses de bajo consumo no pueden distinguir eficiencia de desocupación sin información adicional.
- Una evaluación real necesita más hogares, validación fuera de muestra y una referencia externa de eficiencia.

## 16. Bloque de reproducibilidad

Cada ejecución del pipeline registra en `label_metadata.json`:

- `run_id`: timestamp ISO 8601 UTC correspondiente al cierre de la corrida.
- `input_hashes.household_sensors_zip_sha256`: SHA-256 del ZIP de sensores.
- `input_hashes.ideal_metadata_zip_sha256`: SHA-256 del ZIP de metadata.
- `script_hashes.de_zip_a_category_local_py_sha256`: SHA-256 del script paralelo.
- `script_hashes.de_zip_a_category_cuaderno_py_sha256`: SHA-256 del cuaderno secuencial.
- `audit_sidecar`: contrato del sidecar `ideal_monthly_audit.parquet`
  (ruta, filas, columnas, claves 1:1 con el canónico, disjunto de las features).

Para auditar una entrega concreta se debe ejecutar:

```bash
sha256sum data/processed/*.parquet data/processed/*.csv data/processed/*.json
```

y comparar contra `data/processed/SHA256SUMS`. Cualquier diferencia indica
que los artefactos fueron regenerados o modificados después de la corrida.

Los hashes de entrada y de scripts permiten confirmar que dos corridas
distintas partieron de los mismos insumos y del mismo código metodológico;
`run_id` y los tiempos de ejecución son los únicos campos esperados como
no reproducibles.
