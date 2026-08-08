DEPLOYMENT.md (cómo ejecutar el proyecto localmente y cómo desplegarlo en OCI).




# ⚡ EnergiAI

Sistema inteligente para el análisis de eficiencia energética residencial mediante Inteligencia Artificial.

---

## 📖 Descripción

EnergiAI es un proyecto desarrollado como solución para estimar la categoría de eficiencia energética de una vivienda a partir de información sobre su consumo eléctrico y características generales del inmueble.

El sistema integra un modelo de Machine Learning entrenado en Python y exportado a ONNX para su consumo desde una API REST desarrollada en Spring Boot. Posteriormente, esta API será consumida por una aplicación Frontend para ofrecer una experiencia amigable al usuario final.

---

## 🎯 Objetivo

Desarrollar una solución de Inteligencia Artificial capaz de analizar patrones de consumo energético residencial y clasificar viviendas en diferentes categorías de eficiencia energética, proporcionando además información útil para apoyar la toma de decisiones relacionadas con el ahorro energético.

---

# 🏗 Arquitectura del Proyecto

```
                 Usuario
                     │
                     ▼
              Frontend Web
                     │
                     ▼
          Spring Boot REST API
                     │
                     ▼
             ONNX Runtime Java
                     │
                     ▼
      Modelo de Machine Learning
                     │
                     ▼
        Predicción de categoría
```

---

# 🚀 Tecnologías utilizadas

## Ciencia de Datos

- Python 3.12
- Pandas
- NumPy
- Scikit-Learn
- ONNX
- ONNX Runtime
- Joblib

## Backend

- Java 17
- Spring Boot
- Maven
- ONNX Runtime Java
- OpenAPI (Swagger)

## Frontend

- JavaScript
- HTML5
- CSS3

*(La implementación del Frontend se encuentra en desarrollo.)*

---

# 📂 Estructura del proyecto

```
EnergiAI/

├── data/
│   └── processed/
│
├── docs/
│
├── models/
│
├── notebooks/
│
├── reports/
│
├── scripts/
│
├── backend_V1.0/
│
└── README.md
```

---

# 🔄 Flujo general

1. Limpieza de datos.
2. Ingeniería de características.
3. Entrenamiento del modelo.
4. Evaluación del modelo.
5. Exportación a formato ONNX.
6. Integración del modelo en Spring Boot.
7. Exposición mediante API REST.
8. Consumo desde el Frontend.

---

# 🤖 Modelo de Inteligencia Artificial

Modelo seleccionado:

- Regresión Logística

Variables de entrada:

- consumo_kwh
- uso_horario_pico
- cantidad_equipos
- tipo_inmueble
- horas_alto_consumo

Salida:

- Categoría energética
- Probabilidad por categoría

Categorías:

- Eficiente
- Moderado
- Ineficiente

---

# 📊 Resultados

Durante las pruebas finales del modelo se obtuvo:

- Accuracy: 94.35 %
- F1 Macro: 94.42 %

Estos resultados fueron posteriormente validados utilizando ONNX Runtime para asegurar que las predicciones del modelo exportado fueran equivalentes a las obtenidas durante el entrenamiento.

---

# 🔌 API REST

El Backend expone endpoints para:

- análisis individual mediante JSON
- análisis masivo mediante CSV

La documentación completa de la API se encuentra disponible en:

```
docs/backend_api.md
```

---

# 📚 Documentación

La documentación del proyecto se organiza de la siguiente manera:

| Documento | Descripción |
|------------|-------------|
| README.md | Descripción general del proyecto |
| architecture.md | Arquitectura del sistema |
| data_science.md | Metodología de Ciencia de Datos |
| backend_api.md | Documentación de la API |
| model.md | Modelo de Machine Learning |
| deployment.md | Despliegue |
| user_manual.md | Manual de usuario |
| technical_manual.md | Manual técnico |

---

# 👥 Equipo

Proyecto desarrollado por el Grupo 9 del programa LATAM.

---

# 📄 Licencia

Este proyecto fue desarrollado con fines académicos.