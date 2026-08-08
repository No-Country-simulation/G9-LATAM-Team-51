# 🏗 Arquitectura del Sistema

## Introducción

EnergiAI está compuesto por tres componentes principales que trabajan de forma integrada:

- Ciencia de Datos (Machine Learning)
- Backend (API REST)
- Frontend (Interfaz de Usuario)

Cada uno cumple una función específica dentro del flujo de procesamiento de la información.

---

# Arquitectura General

```
                    Usuario
                        │
                        ▼
                Frontend Web
                        │
          HTTP (JSON / CSV)
                        │
                        ▼
             Spring Boot REST API
                        │
                        ▼
             ONNX Runtime (Java)
                        │
                        ▼
      Modelo de Machine Learning (.onnx)
                        │
                        ▼
            Predicción del modelo
                        │
                        ▼
            Respuesta al Frontend
```

---

# Componentes del sistema

## 1. Ciencia de Datos

Responsable de:

- Preparación y limpieza de datos.
- Análisis exploratorio.
- Ingeniería de características.
- Entrenamiento del modelo.
- Evaluación del modelo.
- Exportación del modelo a formato ONNX.

Principales herramientas:

- Python
- Pandas
- NumPy
- Scikit-Learn
- ONNX
- Joblib

---

## 2. Backend

El Backend fue desarrollado utilizando Spring Boot.

Sus responsabilidades son:

- Exponer la API REST.
- Validar las solicitudes del usuario.
- Ejecutar el modelo ONNX.
- Procesar las probabilidades obtenidas.
- Generar la respuesta final.

Tecnologías:

- Java 25
- Spring Boot
- Maven
- ONNX Runtime Java

---

## 3. Frontend

El Frontend consume la API REST.

Funciones principales:

- Capturar los datos del usuario.
- Enviar solicitudes al Backend.
- Mostrar los resultados.
- Presentar recomendaciones.
- Mostrar probabilidades de manera amigable.

---

# Flujo de procesamiento

## Paso 1

El usuario ingresa los datos de consumo energético.

↓

## Paso 2

El Frontend envía una petición HTTP al Backend.

↓

## Paso 3

Spring Boot valida todos los datos recibidos.

↓

## Paso 4

El Backend construye los tensores requeridos por ONNX Runtime.

↓

## Paso 5

El modelo realiza la inferencia.

↓

## Paso 6

Se obtiene:

- categoría
- probabilidades

↓

## Paso 7

El Backend agrega información complementaria.

Ejemplo:

- recomendaciones
- costo estimado mensual

↓

## Paso 8

Se devuelve la respuesta al Frontend.

---

# Estructura del repositorio

```
EnergiAI/

backend_V1.0/
├── pom.xml
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/example/demo/
│   │   │       ├── controller/
│   │   │       ├── dto/
│   │   │       ├── exception/
│   │   │       └── service/
│   │   └── resources/
│   │       ├── application.properties
│   │       └── models/
│   │           └── energy_efficiency_classifier_v1.onnx
│   └── test/
└── target/
```

---

# Comunicación entre componentes

```
Frontend
      │
      │ JSON
      ▼

Spring Boot

      │

ONNX Runtime

      │

Modelo IA

      │

Predicción

      │

Respuesta JSON

      ▼

Frontend
```

---

# Diagrama de responsabilidades

| Componente | Responsabilidad |
|------------|-----------------|
| Data Science | Construcción y entrenamiento del modelo |
| Backend | Integración del modelo y exposición mediante API |
| Frontend | Interfaz de usuario y visualización de resultados |

---

# Beneficios de la arquitectura

- Separación clara de responsabilidades.
- Independencia entre entrenamiento e inferencia.
- Modelo portable gracias a ONNX.
- Backend desacoplado del proceso de entrenamiento.
- Escalabilidad para futuras mejoras.
- Facilidad para desplegar en diferentes entornos.

---

# Futuras mejoras

- Autenticación de usuarios.
- Historial de análisis.
- Panel de métricas.
- Nuevos modelos de clasificación.
- Integración con servicios en la nube.