# Changelog

Todos los cambios importantes del proyecto serán documentados en este archivo.

El formato está inspirado en **Keep a Changelog** y sigue principios de versionado semántico.

---

## [1.0.0] - 2026-07

### Added

#### Data Science

- Pipeline completo de limpieza de datos.
- Ingeniería de características.
- Metodología de etiquetado `ideal-relative-v1`.
- Entrenamiento del modelo de clasificación.
- Exportación del modelo a formato ONNX.
- Exportación del pipeline en Joblib.
- Reportes de evaluación del modelo.
- Validación de paridad entre Scikit-Learn y ONNX.

---

#### Backend

- API REST desarrollada con Spring Boot.
- Integración con ONNX Runtime.
- Endpoint para inferencia mediante JSON.
- Endpoint para procesamiento masivo mediante archivos CSV.
- Validaciones de entrada.
- Manejo centralizado de excepciones.
- Documentación técnica del contrato entre Backend y Data Science.

---

#### Documentación

- README principal.
- Documentación de entrenamiento.
- Definición de categorías.
- Guía de integración ONNX.
- Documentación del dataset.
- Guía de contribución.

---

## [0.5.0]

### Added

Primera integración funcional entre Backend y modelo ONNX.

Se implementó:

- carga inicial del modelo;
- primeras pruebas de inferencia;
- estructura inicial del backend.

---

## [0.1.0]

### Added

Inicio del proyecto.

Se incorporaron:

- estructura inicial del repositorio;
- primeros notebooks exploratorios;
- limpieza inicial del dataset;
- primeros experimentos de entrenamiento.

---

# Próximas versiones

## 1.1.0

Planeado:

- Despliegue en Oracle Cloud Infrastructure (OCI).
- Integración completa con Frontend.
- Mejoras visuales.
- Dashboard de consumo.
- Optimización de respuestas de la API.
- Nuevas pruebas de integración.

---

## Historial de versiones

| Versión | Estado |
|----------|--------|
| 0.1.0 | Inicio del proyecto |
| 0.5.0 | Primera integración |
| 1.0.0 | Integración completa Data Science + Backend |
| 1.1.0 | Despliegue e integración Frontend (planeado) |

## [1.0.1] - 2026-08

### Changed

#### Backend
- Reorganización de la estructura de `backend_V1.0`.
- Actualización del contrato de entrada de la API.
- Endpoint principal disponible bajo `/api/analisis-energetico`.
- Incorporación del endpoint `/api/analisis-energetico/csv`.
- Actualización de la respuesta de análisis con probabilidades por clase, recomendaciones y costo estimado.
- Carga del modelo ONNX desde los recursos del classpath mediante `ClassPathResource`.
- Ajustes para el despliegue de la aplicación con el modelo ONNX incluido como recurso.