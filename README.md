# ⚡ EnergiAI

Sistema inteligente para el análisis de eficiencia energética residencial mediante Inteligencia Artificial.

---

## 📖 Descripción

**EnergiAI** analiza información relacionada con el consumo eléctrico y las características de una vivienda para estimar su categoría de eficiencia energética.

El proyecto integra:

- Un modelo de Machine Learning desarrollado en Python.
- El modelo exportado a formato **ONNX**.
- Una API REST desarrollada con **Spring Boot**.
- **ONNX Runtime** para ejecutar las predicciones desde el backend.
- Un Frontend destinado a presentar los resultados de forma amigable al usuario.

---

## 🎯 Objetivo

Clasificar viviendas según su nivel de eficiencia energética y proporcionar información adicional que ayude al usuario a comprender su consumo y tomar decisiones orientadas al ahorro energético.

Las categorías utilizadas por el sistema son:

- **Eficiente**
- **Moderado**
- **Ineficiente**

---

## 🏗️ Arquitectura general

```text
                 Usuario
                    │
                    ▼
              Frontend Web
                    │
                    ▼
            Spring Boot API
                    │
                    ▼
             ONNX Runtime
                    │
                    ▼
              Modelo ONNX
                    │
                    ▼
          Predicción energética
````

El Frontend consume la API REST y el backend utiliza el modelo ONNX para realizar las predicciones.

---

## 🛠️ Tecnologías

### Ciencia de Datos

* Python 3.12
* Pandas
* NumPy
* Scikit-Learn
* ONNX
* ONNX Runtime
* Joblib

### Backend

* Java 25
* Spring Boot
* Maven
* ONNX Runtime Java
* OpenAPI / Swagger

### Frontend

* JavaScript
* HTML5
* CSS3

> El Frontend se encuentra en proceso de integración con la API.

---

## 📂 Estructura principal

```text
G9-LATAM-Team-51/
│
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
│   ├── src/
│   ├── pom.xml
│   └── mvnw
│
└── README.md
```

La estructura puede evolucionar durante el desarrollo del proyecto.

---

## 🔄 Flujo del sistema

```text
Datos de entrada
      │
      ▼
Procesamiento de datos
      │
      ▼
Entrenamiento del modelo
      │
      ▼
Exportación a ONNX
      │
      ▼
Integración con Spring Boot
      │
      ▼
API REST
      │
      ▼
Frontend
      │
      ▼
Resultado para el usuario
```

---

## 🤖 Modelo de Inteligencia Artificial - Regresión Logística

El modelo utilizado actualmente es un clasificador basado en **Regresión Logística**.

### Variables de entrada

La API recibe cinco variables principales:

| Variable           | Descripción                               |
| ------------------ | ----------------------------------------- |
| `consumoKwh`       | Consumo energético                        |
| `usoHorarioPico`   | Indica si existe uso durante horario pico |
| `cantidadEquipos`  | Cantidad de equipos eléctricos            |
| `tipoInmueble`     | Tipo de vivienda                          |
| `horasAltoConsumo` | Horas de alto consumo                     |

El modelo genera una categoría energética y las probabilidades asociadas a cada clase.

---

## 🔌 API REST

El backend expone actualmente dos operaciones principales:

### Análisis individual

```text
POST /api/analisis-energetico
```

Permite enviar los datos de una vivienda mediante JSON.

### Análisis mediante CSV

```text
POST /api/analisis-energetico/csv
```

Permite procesar múltiples registros mediante un archivo CSV.

La referencia completa de requests, responses y formatos aceptados se encuentra en:

`docs/API_REFERENCE.md`

---

## 💰 Información adicional

Además de la clasificación energética, el backend calcula un costo estimado mensual a partir del consumo recibido.

La respuesta también puede incluir:

* Categoría energética.
* Probabilidad de la categoría.
* Probabilidades por clase.
* Recomendaciones.
* Costo estimado mensual.

---

## 🚀 Ejecución del proyecto

La ejecución local del backend y el despliegue en Oracle Cloud Infrastructure (OCI) se encuentran documentados en:

`docs/DEPLOYMENT.md`

---

## 🧪 Pruebas

Las instrucciones para ejecutar y validar las pruebas de la API y del modelo se encuentran en:

`docs/TESTING.md`

---

## 📚 Documentación

La documentación técnica se encuentra en la carpeta `docs/`:

| Documento                 | Descripción                                            |
| ------------------------- | ------------------------------------------------------ |
| `API_REFERENCE.md`        | Endpoints, requests y responses principales de la API. |
| `ARCHITECTURE.md`         | Arquitectura general y flujo de datos del sistema.     |
| `DEPLOYMENT.md`           | Ejecución local y despliegue en OCI.                   |
| `TESTING.md`              | Pruebas y validación de la API y del modelo.           |
| `backend_onnx_handoff.md` | Integración entre el modelo ONNX y el backend.         |
| `category_definition.md`  | Definición de las categorías de eficiencia energética. |
| `model_training.md`       | Proceso de entrenamiento y evaluación del modelo.      |

---

## 📊 Resultados del modelo

Durante la evaluación del modelo se obtuvieron los siguientes resultados:

* **Accuracy:** 94.35 %
* **F1 Macro:** 94.42 %

La documentación relacionada con el entrenamiento y evaluación se encuentra en:

`docs/model_training.md`

---

## ☁️ Despliegue

El backend actual se encuentra preparado para su ejecución mediante Spring Boot y utiliza el modelo ONNX como recurso de la aplicación.

El despliegue del backend se realiza en **Oracle Cloud Infrastructure (OCI)**.

Para conocer los pasos de ejecución y despliegue:

`docs/DEPLOYMENT.md`

---

## 👥 Equipo

Proyecto desarrollado por el **Grupo 9 – LATAM**.

---

## 📄 Licencia

Proyecto desarrollado con fines académicos.

```