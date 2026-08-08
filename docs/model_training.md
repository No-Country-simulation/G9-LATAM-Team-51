# Model Training Documentation

## Objetivo

Este documento describe el proceso completo utilizado para construir el modelo de clasificación de eficiencia energética.

Incluye las etapas de preparación de datos, entrenamiento, evaluación, selección del modelo y exportación para producción.

---

# Flujo general

El pipeline de Machine Learning siguió las siguientes etapas:

```
Datos originales
        │
        ▼
Limpieza de datos
        │
        ▼
Ingeniería de características
        │
        ▼
Etiquetado relativo
        │
        ▼
Entrenamiento de modelos
        │
        ▼
Validación cruzada
        │
        ▼
Evaluación en Test
        │
        ▼
Exportación ONNX
        │
        ▼
Integración Backend
```

---

# Dataset

Fuente:

```
IDEAL Household Energy Dataset
```

Después del proceso de limpieza se obtuvieron:

| Conjunto | Registros |
|----------|----------:|
| Train | 431 |
| Test | 124 |
| Total | 555 |

Se utilizaron 127 viviendas.

---

# Variables utilizadas

El modelo utiliza cinco variables de entrada.

| Variable | Tipo |
|----------|------|
| consumo_kwh | Numérica |
| uso_horario_pico | Binaria |
| cantidad_equipos | Entera |
| tipo_inmueble | Categórica |
| horas_alto_consumo | Entera |

Variable objetivo:

```
categoria
```

---

# Etiquetado

Las categorías fueron generadas utilizando la metodología:

```
ideal-relative-v1
```

Categorías:

- Eficiente
- Moderado
- Ineficiente

Estas categorías representan una clasificación relativa dentro del conjunto de datos y no corresponden a certificaciones energéticas oficiales.

---

# División del conjunto de datos

Para evitar fuga de información entre registros pertenecientes a una misma vivienda se utilizó:

```
Group Shuffle Split
```

Posteriormente, el conjunto de entrenamiento fue evaluado mediante:

```
StratifiedGroupKFold
```

con:

- 5 folds

Esto permitió mantener tanto el equilibrio entre clases como la separación por vivienda.

---

# Modelos evaluados

Durante el entrenamiento se compararon distintos algoritmos de clasificación.

La selección final se realizó utilizando el valor más alto de F1 Macro promedio obtenido mediante validación cruzada.

Modelo seleccionado:

```
Logistic Regression
```

---

# Hiperparámetros

Modelo final:

```
LogisticRegression
```

Parámetros:

| Parámetro | Valor |
|-----------|-------|
| C | 10.0 |
| max_iter | 3000 |
| random_state | 42 |
| class_weight | None |

---

# Métricas finales

Resultados sobre el conjunto Test.

| Métrica | Valor |
|---------|-------:|
| Accuracy | 0.9435 |
| Balanced Accuracy | 0.9510 |
| F1 Macro | 0.9442 |
| F1 Weighted | 0.9439 |

---

# Exportación del modelo

El modelo fue exportado en dos formatos.

## Joblib

Utilizado para reproducibilidad del entrenamiento.

```
energy_efficiency_pipeline_v1.joblib
```

---

## ONNX

Utilizado por la aplicación Java para inferencia en producción.

```
energy_efficiency_classifier_v1.onnx
```

---

# Validación ONNX

Se verificó la equivalencia entre el modelo de Scikit-Learn y el modelo ONNX.

Resultados:

- Coincidencia de etiquetas: 100%
- Diferencia máxima de probabilidades: 1.11e-16

Lo anterior garantiza que el backend produce exactamente las mismas predicciones obtenidas durante el entrenamiento.

---

# Reproducibilidad

El proyecto fija las versiones principales de las librerías utilizadas.

| Librería | Versión |
|----------|----------|
| Python | 3.12.7 |
| NumPy | 2.2.6 |
| Pandas | 2.3.3 |
| Scikit-Learn | 1.7.2 |
| ONNX | 1.19.0 |
| ONNX Runtime | 1.23.2 |

---

# Archivos principales

```
notebooks/
│
├── 01_limpieza_ideal.ipynb
├── 02_eda_ideal.ipynb
└── 03_entrenamiento_evaluacion.ipynb
```

```
scripts/
└── export_model_artifacts.py
```

```
models/
├── energy_efficiency_classifier_v1.onnx
├── energy_efficiency_pipeline_v1.joblib
└── model_contract_v1.json
```

```
reports/
├── final_test_metrics.json
├── onnx_parity_report.json
└── onnx_prediction_examples.json
```

---

# Limitaciones

- El modelo fue entrenado utilizando datos del conjunto IDEAL.
- La metodología de etiquetado es relativa al conjunto de entrenamiento.
- La generalización hacia otros países o contextos requiere validación adicional.
- Las categorías obtenidas no representan una certificación energética oficial.

---

# Próximos pasos

Como trabajo futuro se propone:

- incorporar nuevas variables relacionadas con hábitos de consumo;
- evaluar modelos basados en árboles de decisión y técnicas de ensamble;
- ampliar el conjunto de datos con viviendas de otras regiones;
- implementar monitoreo del desempeño del modelo en producción.