# Entrenamiento y evaluación de modelos

**Responsable:** Tomás Maldonado (TM)

**Fecha de ejecución:** 21 de julio de 2026

**Dataset canónico:** `data/processed/ideal_monthly_features_labeled.parquet`

**Versión metodológica de etiquetas:** `ideal-relative-v1`

## Objetivo

Entrenar y comparar modelos supervisados capaces de clasificar un hogar-mes
como `Eficiente`, `Moderado` o `Ineficiente` a partir de las cinco variables
definidas en el contrato del endpoint.

## Variables utilizadas

Los únicos predictores son:

1. `consumo_kwh`
2. `uso_horario_pico`
3. `cantidad_equipos`
4. `tipo_inmueble`
5. `horas_alto_consumo`

La variable objetivo es `categoria`. `homeid` se utiliza exclusivamente para
agrupar viviendas durante la validación cruzada. No se usan como predictores
`score`, percentiles, componentes de la pseudoetiqueta, columnas de cobertura,
auditoría, identificadores ni fechas.

## Validaciones de entrada

- 555 filas hogar-mes y 151 viviendas.
- 431 filas / 113 viviendas en `train`.
- 124 filas / 38 viviendas en `test`.
- Cero viviendas compartidas entre `train` y `test`.
- Cero nulos en columnas obligatorias.
- Cero duplicados por `(homeid, year_month)`.
- Tres categorías presentes en ambos splits.

Distribución por split:

| Split | Eficiente | Moderado | Ineficiente |
| --- | ---: | ---: | ---: |
| Train | 144 | 143 | 144 |
| Test | 53 | 38 | 33 |

## Preprocesamiento

- Variables numéricas: imputación por mediana y `StandardScaler`.
- `tipo_inmueble` y `uso_horario_pico`: imputación por moda y
  `OneHotEncoder(handle_unknown="ignore")`.
- Todo el preprocesamiento vive dentro de un `Pipeline` para ajustarse solo con
  los datos de cada fold y evitar leakage.

## Estrategia de evaluación

1. Se conserva el split oficial por hogar entregado con el dataset.
2. La selección de modelo utiliza únicamente las 431 filas de entrenamiento.
3. Se aplica `StratifiedGroupKFold` con 5 folds, `homeid` como grupo,
   `shuffle=True` y `random_state=42`.
4. La métrica principal es F1 macro.
5. El conjunto de test se evalúa una sola vez después de elegir el ganador.

## Modelos comparados

| Modelo | F1 macro CV | Desviación | Accuracy CV |
| --- | ---: | ---: | ---: |
| Regresión Logística | 0.9554 | 0.0256 | 0.9614 |
| Random Forest | 0.9454 | 0.0141 | 0.9502 |
| Árbol de Decisión | 0.9162 | 0.0366 | 0.9301 |
| Modelo base (`DummyClassifier`) | 0.1076 | 0.0245 | 0.1947 |

Los valores completos y parámetros de cada búsqueda están disponibles en
`reports/cv_model_comparison.csv`.

## Modelo seleccionado

Se seleccionó **Regresión Logística** porque obtuvo el mayor F1 macro promedio
en validación cruzada agrupada.

Parámetros ganadores:

```text
C = 10.0
class_weight = None
max_iter = 3000
random_state = 42
```

## Resultado final sobre test

| Métrica | Resultado |
| --- | ---: |
| Accuracy | 0.9435 |
| Balanced accuracy | 0.9510 |
| F1 macro | 0.9442 |
| F1 weighted | 0.9439 |

Resultados por categoría:

| Categoría | Precision | Recall | F1 | Registros |
| --- | ---: | ---: | ---: | ---: |
| Eficiente | 1.0000 | 0.9057 | 0.9505 | 53 |
| Moderado | 0.8780 | 0.9474 | 0.9114 | 38 |
| Ineficiente | 0.9429 | 1.0000 | 0.9706 | 33 |

Matriz de confusión, en orden `Eficiente`, `Moderado`, `Ineficiente`:

```text
[[48, 5, 0],
 [ 0,36, 2],
 [ 0, 0,33]]
```

El modelo clasificó correctamente 117 de los 124 registros de prueba.

## Importancia descriptiva por permutación

| Variable | Disminución media de F1 macro |
| --- | ---: |
| `consumo_kwh` | 0.4962 |
| `uso_horario_pico` | 0.2441 |
| `horas_alto_consumo` | 0.1618 |
| `tipo_inmueble` | 0.1235 |
| `cantidad_equipos` | 0.0304 |

Esta importancia describe el comportamiento del modelo; no demuestra
causalidad.

## Pruebas funcionales

Se ejecutaron tres predicciones con registros de test, una por categoría. El
pipeline recibió solo las cinco variables del endpoint y devolvió la categoría
correcta junto con la probabilidad máxima. Los casos se conservan en
`reports/prediction_examples.csv`.

## Artefactos entregados

- `notebooks/03_entrenamiento_evaluacion.ipynb`
- `notebooks/03_entrenamiento_evaluacion.py`
- `reports/cv_model_comparison.csv`
- `reports/cv_model_comparison.png`
- `reports/final_test_metrics.json`
- `reports/classification_report.csv`
- `reports/confusion_matrix.csv`
- `reports/confusion_matrix.png`
- `reports/feature_importance.csv`
- `reports/feature_importance.png`
- `reports/prediction_examples.csv`
- `requirements-model.txt`

## Reproducción

Desde la raíz del repositorio:

```bash
python -m venv .venv
python -m pip install -r requirements-model.txt
python notebooks/03_entrenamiento_evaluacion.py
```

En Windows puede ejecutarse sin activar el entorno:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-model.txt
.\.venv\Scripts\python.exe notebooks\03_entrenamiento_evaluacion.py
```

## Alcance de serialización

Por acuerdo del equipo, esta entrega no incluye `.joblib`, `.onnx` ni cambios
en la API. La serialización, la integración con Java/Spring Boot y el despliegue
en OCI quedan bajo responsabilidad del equipo de Back-End/DevOps. El notebook
deja el pipeline seleccionado disponible como `best_model` al finalizar la
ejecución.

## Limitaciones

- Las categorías son pseudoetiquetas construidas a partir de las mismas cinco
  variables; las métricas miden qué tan bien el modelo reproduce esa regla.
- No son certificaciones energéticas oficiales ni son aptas para facturación.
- Los datos corresponden a hogares de Edimburgo entre 2016 y 2018.
- La generalización a Latinoamérica requiere validación externa.
- Sin información observada de ocupación no puede distinguirse por completo un
  hogar eficiente de un hogar temporalmente desocupado.
