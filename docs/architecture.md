# Arquitectura del sistema

## 1. Visión general

El sistema está compuesto por tres partes principales:

- **Frontend:** interfaz utilizada por el usuario para ingresar los datos y visualizar el análisis.
- **Backend:** API REST desarrollada con Spring Boot que recibe las solicitudes, valida los datos y ejecuta el modelo.
- **Modelo ONNX:** modelo de Machine Learning utilizado por el backend para clasificar el consumo energético.

El flujo principal es:

```text
┌──────────────┐
│    Usuario   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Frontend   │
│   Interfaz   │
└──────┬───────┘
       │ HTTP / JSON
       ▼
┌────────────────────────┐
│       Backend          │
│      Spring Boot       │
│                        │
│  Controller → Service  │
└───────────┬────────────┘
            │
            ▼
┌─────────────────────────┐
│      Modelo ONNX        │
│ Clasificación energética│
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Resultado del análisis  │
│ categoría + probabilidad│
│ recomendaciones + costo │
└───────────┬─────────────┘
            │
            ▼
       Frontend / Usuario
````

---

## 2. Componentes

### Frontend

Responsable de:

* Recopilar los datos ingresados por el usuario.
* Enviar las solicitudes al backend.
* Mostrar la categoría energética obtenida.
* Mostrar probabilidades, recomendaciones y costo estimado.

El frontend consume la API REST del backend.

> El frontend se encuentra actualmente en desarrollo/integración y sus cambios todavía pueden evolucionar.

---

### Backend

El backend está desarrollado con:

* Java
* Spring Boot
* Spring Web MVC
* ONNX Runtime

Su estructura principal es:

```text
backend_V1.0/
└── src/
    └── main/
        ├── java/
        │   └── com/example/demo/
        │       ├── controller/
        │       ├── dto/
        │       ├── exception/
        │       └── service/
        │
        └── resources/
            └── models/
                └── energy_efficiency_classifier_v1.onnx
```

### Responsabilidad de cada capa

```text
Controller
    │
    │ recibe HTTP
    ▼
DTO
    │
    │ representa los datos
    ▼
Service
    │
    │ valida + prepara entrada
    ▼
ONNX Runtime
    │
    │ ejecuta modelo
    ▼
AnalisisResponse
    │
    ▼
Respuesta JSON
```

---

## 3. Flujo de una predicción

Para una predicción individual:

```text
1. Usuario ingresa datos
          ↓
2. Frontend crea JSON
          ↓
3. POST /api/analisis-energetico
          ↓
4. AnalisisController recibe la petición
          ↓
5. ConsumoRequest representa los datos
          ↓
6. OnnxInferenceService valida los valores
          ↓
7. Se ejecuta el modelo ONNX
          ↓
8. Se obtiene la categoría y probabilidades
          ↓
9. Se generan recomendaciones
          ↓
10. Se calcula el costo estimado
          ↓
11. AnalisisResponse
          ↓
12. Frontend muestra el resultado
```

---

## 4. Flujo de procesamiento CSV

El backend también permite procesar múltiples registros mediante un archivo CSV.

```text
CSV
 │
 ▼
POST /api/analisis-energetico/csv
 │
 ▼
Validación del encabezado
 │
 ▼
Lectura de registros
 │
 ▼
ConsumoRequest por registro
 │
 ▼
Modelo ONNX
 │
 ▼
AnalisisResponse por registro
 │
 ▼
CsvAnalysisResponse
```

La respuesta contiene:

* `totalRecords`
* `results`

Cada elemento de `results` contiene el mismo tipo de información que una predicción individual.

---

## 5. Modelo de Machine Learning

El backend utiliza el siguiente modelo:

```text
energy_efficiency_classifier_v1.onnx
```

El modelo recibe cinco variables:

| Variable           | Tipo           |
| ------------------ | -------------- |
| `consumoKwh`       | número decimal |
| `usoHorarioPico`   | booleano       |
| `cantidadEquipos`  | entero         |
| `tipoInmueble`     | texto          |
| `horasAltoConsumo` | entero         |

Las categorías posibles son:

```text
Eficiente
Ineficiente
Moderado
```

El backend obtiene del modelo:

* Categoría predicha.
* Probabilidad de la categoría.
* Probabilidades por cada clase.

---

## 6. Respuesta del sistema

El backend transforma la predicción del modelo en una respuesta orientada al usuario.

Conceptualmente:

```text
Modelo ONNX
     │
     ├── categoría
     ├── probabilidades
     │
     ▼
Backend
     │
     ├── recomendaciones
     ├── costo estimado
     │
     ▼
Respuesta JSON
     │
     ▼
Frontend
```

Esto permite separar la lógica del modelo de la presentación final al usuario.

---

## 7. Manejo de errores

El backend centraliza los errores mediante `ApiExceptionHandler`.

Los principales casos contemplados son:

* Datos de entrada inválidos.
* Archivo CSV vacío.
* Encabezado CSV incorrecto.
* Formato inválido en los registros.
* Error durante la ejecución del modelo.
* Modelo ONNX no disponible o no cargable.

Las respuestas de error utilizan una estructura sencilla:

```json
{
  "error": "Bad Request",
  "message": "Descripción del problema"
}
```

---

## 8. Despliegue

El backend actualizado de la rama `backend1.0` ya fue preparado y desplegado en **OCI (Oracle Cloud Infrastructure)**.

La arquitectura de despliegue mantiene el mismo flujo lógico:

```text
Usuario
   │
   ▼
Frontend
   │
   │ HTTP
   ▼
Backend desplegado en OCI
   │
   ▼
Modelo ONNX
   │
   ▼
Respuesta
```

El frontend deberá integrarse con la instancia del backend desplegado para completar el flujo de extremo a extremo.

---

## 9. Principio de separación

La solución mantiene separadas las responsabilidades:

```text
Frontend
   → presentación

Backend
   → API + validación + lógica de integración

Modelo ONNX
   → predicción

OCI
   → infraestructura de despliegue
```

Esta separación facilita que cada componente pueda evolucionar sin modificar innecesariamente los demás.

---

## 10. Estado actual

| Componente                     | Estado                    |
| ------------------------------ | ------------------------- |
| Modelo ONNX                    | ✅ Integrado               |
| Backend Spring Boot            | ✅ Actualizado             |
| API REST                       | ✅ Implementada            |
| Endpoint JSON                  | ✅ Implementado            |
| Endpoint CSV                   | ✅ Implementado            |
| Manejo de errores              | ✅ Implementado            |
| Backend en OCI                 | ✅ Desplegado              |
| Frontend                       | 🔄 En desarrollo          |
| Integración Frontend + Backend | 🔄 Pendiente de completar |

```