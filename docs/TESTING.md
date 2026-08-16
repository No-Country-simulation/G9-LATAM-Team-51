# Testing

## 1. Objetivo

Las pruebas permiten comprobar que el backend puede iniciar correctamente, que la API acepta los datos esperados y que el modelo ONNX devuelve resultados válidos.

Actualmente el proyecto cuenta con una prueba básica de contexto de Spring Boot.

---

## 2. Prueba actual del backend

La prueba se encuentra en:

```text
backend/src/test/java/com/example/demo/DemoApplicationTests.java
````

Actualmente verifica que el contexto de la aplicación pueda cargarse correctamente.

Para ejecutarla desde la carpeta `backend_V1.0`:

```bash
./mvnw test
```

En Windows:

```bash
mvnw.cmd test
```

Si la prueba finaliza correctamente, Maven mostrará:

```text
BUILD SUCCESS
```

---

## 3. Validación de la API

Además de la prueba automática de contexto, la API puede validarse realizando peticiones HTTP.

### Endpoint JSON

```text
POST /api/analisis-energetico
```

Ejemplo de solicitud:

```json
{
  "consumoKwh": 250.0,
  "usoHorarioPico": true,
  "cantidadEquipos": 5,
  "tipoInmueble": "Casa",
  "horasAltoConsumo": 6
}
```

La respuesta debe contener:

* `categoria`
* `probabilidad`
* `probabilitiesByClass`
* `recomendaciones`
* `costoEstimadoMensual`

La categoría debe corresponder a una de las clases disponibles:

```text
Eficiente
Moderado
Ineficiente
```

---

## 4. Validación del CSV

También se puede probar:

```text
POST /api/analisis-energetico/csv
```

enviando un archivo mediante `multipart/form-data` con el campo:

```text
file
```

El CSV debe utilizar exactamente estos encabezados:

```text
consumoKwh,usoHorarioPico,cantidadEquipos,tipoInmueble,horasAltoConsumo
```

La respuesta debe incluir:

```json
{
  "totalRecords": 1,
  "results": []
}
```

`results` contendrá el análisis correspondiente a cada registro procesado.

---

## 5. Validaciones importantes

Se deben comprobar especialmente estos casos:

| Caso                                                | Resultado esperado    |
| --------------------------------------------------- | --------------------- |
| Solicitud válida                                    | `200 OK` con análisis |
| `consumoKwh` menor o igual a 0                      | `400 Bad Request`     |
| `cantidadEquipos` menor que 1                       | `400 Bad Request`     |
| `tipoInmueble` diferente de `Casa` o `Departamento` | `400 Bad Request`     |
| `horasAltoConsumo` fuera de 0–24                    | `400 Bad Request`     |
| CSV vacío                                           | `400 Bad Request`     |
| Encabezado CSV incorrecto                           | `400 Bad Request`     |

Los errores utilizan la estructura:

```json
{
  "error": "Bad Request",
  "message": "Descripción del problema"
}
```

---

## 6. Validación del modelo ONNX

La ejecución del modelo se realiza mediante `OnnxInferenceService`.

La validación básica consiste en comprobar que:

1. El backend puede cargar `energy_efficiency_classifier_v1.onnx`.
2. La petición contiene los cinco campos requeridos.
3. El modelo devuelve una categoría válida.
4. Se reciben las probabilidades de las tres clases.
5. Se generan las recomendaciones.
6. Se obtiene el costo estimado.

Las clases esperadas son:

```text
Eficiente
Ineficiente
Moderado
```

---

## 7. Prueba de extremo a extremo

Una validación completa del sistema sigue este flujo:

```text
Frontend
   ↓
API Backend
   ↓
Validación de datos
   ↓
Modelo ONNX
   ↓
Resultado
   ↓
Frontend
```

Para considerar funcional la integración, se debe comprobar que el resultado recibido por el frontend coincide con la respuesta entregada por la API.

---

## 8. Estado actual del testing

| Área                                           | Estado                      |
| ---------------------------------------------- | --------------------------- |
| Prueba de contexto Spring Boot                 | ✅ Disponible                |
| Validación manual del endpoint JSON            | ✅ Disponible                |
| Validación manual del endpoint CSV             | ✅ Disponible                |
| Validación de entradas inválidas               | ✅ Implementada en backend   |
| Validación del modelo ONNX                     | ✅ Integrada                 |
| Pruebas automatizadas específicas de endpoints | 🔄 Pendiente de ampliar     |
| Pruebas automatizadas específicas del modelo   | 🔄 Pendiente de ampliar     |
| Prueba completa Frontend + Backend             | 🔄 Pendiente de integración |

> Este documento describe las pruebas y validaciones actualmente disponibles. No se consideran implementadas como pruebas automatizadas aquellas que todavía requieren ejecución manual.

````
