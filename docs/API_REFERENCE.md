# API Reference

Referencia rápida de la API de análisis energético del proyecto.

## Base URL

La API utiliza el prefijo:

```text
/api
````

> La URL completa depende del entorno donde esté desplegado el backend. Actualmente el backend se encuentra desplegado en OCI.

---

## 1. Análisis energético — JSON

Permite analizar un registro individual mediante el modelo ONNX.

### Endpoint

```http
POST /api/analisis-energetico
```

### Content-Type

```text
application/json
```

### Request

```json
{
  "consumoKwh": 250.5,
  "usoHorarioPico": true,
  "cantidadEquipos": 8,
  "tipoInmueble": "Casa",
  "horasAltoConsumo": 6
}
```

### Campos

| Campo              | Tipo    | Requerido | Descripción                                    |
| ------------------ | ------- | --------- | ---------------------------------------------- |
| `consumoKwh`       | Number  | Sí        | Consumo energético en kWh. Debe ser mayor a 0. |
| `usoHorarioPico`   | Boolean | Sí        | Indica si existe uso durante horario pico.     |
| `cantidadEquipos`  | Integer | Sí        | Cantidad de equipos. Debe ser al menos 1.      |
| `tipoInmueble`     | String  | Sí        | `Casa` o `Departamento`.                       |
| `horasAltoConsumo` | Integer | Sí        | Horas de alto consumo. Rango de 0 a 24.        |

### Response

```json
{
  "categoria": "Eficiente",
  "probabilidad": 0.9968,
  "probabilitiesByClass": {
    "Eficiente": 0.9968,
    "Ineficiente": 0.0012,
    "Moderado": 0.002
  },
  "recomendaciones": [
    "Mantener las prácticas actuales de consumo.",
    "Revisar si es posible optimizar más con equipos eficientes."
  ],
  "costoEstimadoMensual": 187.88
}
```

### Respuesta

* `categoria`: clasificación obtenida por el modelo.
* `probabilidad`: probabilidad asociada a la categoría seleccionada.
* `probabilitiesByClass`: probabilidades para las tres categorías.
* `recomendaciones`: sugerencias según la categoría.
* `costoEstimadoMensual`: estimación calculada a partir del consumo.

Las categorías posibles son:

```text
Eficiente
Moderado
Ineficiente
```

---

## 2. Análisis energético — CSV

Permite procesar múltiples registros mediante un archivo CSV.

### Endpoint

```http
POST /api/analisis-energetico/csv
```

### Content-Type

```text
multipart/form-data
```

### Campo del formulario

```text
file
```

### Formato esperado

El CSV debe utilizar exactamente estos encabezados:

```csv
consumoKwh,usoHorarioPico,cantidadEquipos,tipoInmueble,horasAltoConsumo
250.5,true,8,Casa,6
180.0,false,5,Departamento,3
320.2,true,10,Casa,8
```

### Response

```json
{
  "totalRecords": 3,
  "results": [
    {
      "categoria": "Eficiente",
      "probabilidad": 0.9968,
      "probabilitiesByClass": {
        "Eficiente": 0.9968,
        "Ineficiente": 0.0012,
        "Moderado": 0.002
      },
      "recomendaciones": [
        "Mantener las prácticas actuales de consumo.",
        "Revisar si es posible optimizar más con equipos eficientes."
      ],
      "costoEstimadoMensual": 187.88
    }
  ]
}
```

`results` contiene una respuesta de análisis por cada registro válido procesado.

---

## 3. Errores

La API devuelve errores en formato JSON.

### Ejemplo

```json
{
  "error": "Bad Request",
  "message": "El campo consumoKwh es obligatorio y debe ser mayor a 0."
}
```

### Códigos principales

| Código | Significado                                    |
| ------ | ---------------------------------------------- |
| `400`  | Datos de entrada inválidos o CSV incorrecto.   |
| `500`  | Error interno durante la ejecución del modelo. |

---

## 4. Validaciones principales

La API valida los datos antes de ejecutar el modelo:

* `consumoKwh` debe ser mayor que `0`.
* `usoHorarioPico` es obligatorio.
* `cantidadEquipos` debe ser al menos `1`.
* `tipoInmueble` debe ser `Casa` o `Departamento`.
* `horasAltoConsumo` debe estar entre `0` y `24`.
* El CSV debe contener exactamente las cinco columnas esperadas.
* No se acepta un archivo CSV vacío.

---

## 5. Flujo general

```text
Cliente
   │
   ├── JSON ────────────────┐
   │                        │
   └── CSV ─────────────────┤
                            ▼
                 /api/analisis-energetico
                            │
                            ▼
                   Validación de datos
                            │
                            ▼
                      Modelo ONNX
                            │
                            ▼
                 Clasificación energética
                            │
                            ▼
                 Respuesta JSON
```

## Nota

La API utiliza el modelo:

```text
energy_efficiency_classifier_v1.onnx
```

El modelo se carga como recurso de la aplicación desde:

```text
src/main/resources/models/
```

La documentación debe mantenerse sincronizada con cualquier cambio en los endpoints, DTOs o estructura de respuesta del backend.

