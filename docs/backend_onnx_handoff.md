# Backend Integration Guide (ONNX)

## Objetivo

Este documento describe el contrato de integración entre el modelo de Machine Learning desarrollado por el equipo de Data Science y la API Java (Spring Boot).

El objetivo es garantizar que el modelo pueda utilizarse desde cualquier implementación del backend sin depender del entorno de entrenamiento en Python.

---

# Modelo utilizado

Modelo exportado:

```
energy_efficiency_classifier_v1.onnx
```

Versión:

```
v1.0.0
```

Algoritmo:

```
Logistic Regression
```

Formato:

```
ONNX
```

---

# Entradas requeridas

El modelo requiere exactamente cinco variables.

| Campo API | Tipo | Descripción |
|-----------|------|-------------|
| consumoKwh | Double | Consumo mensual de energía (kWh) |
| usoHorarioPico | Boolean | Uso frecuente durante horario pico |
| cantidadEquipos | Integer | Número de equipos eléctricos |
| tipoInmueble | String | Casa o Departamento |
| horasAltoConsumo | Integer | Horas diarias de alto consumo |

Ejemplo JSON:

```json
{
  "consumoKwh": 420,
  "usoHorarioPico": true,
  "cantidadEquipos": 10,
  "tipoInmueble": "Casa",
  "horasAltoConsumo": 8
}
```

---
## Transformación de entradas

El backend recibe los datos mediante `ConsumoRequest` y los transforma
al formato esperado por ONNX:

| Campo API | Entrada ONNX |
|-----------|--------------|
| consumoKwh | consumo_kwh |
| usoHorarioPico | uso_horario_pico |
| cantidadEquipos | cantidad_equipos |
| tipoInmueble | tipo_inmueble |
| horasAltoConsumo | horas_alto_consumo |

El backend también convierte `usoHorarioPico` de `Boolean` a `0/1`
antes de ejecutar la inferencia.

---

# Salida del modelo

El modelo devuelve dos salidas ONNX.

## Label

Categoría predicha.

Valores posibles:

- Eficiente
- Moderado
- Ineficiente

---

## Probabilidades

Vector de probabilidades.

Orden EXACTO:

```
[
    "Eficiente",
    "Ineficiente",
    "Moderado"
]
```

Este orden corresponde al tensor generado por ONNX y no debe modificarse.

---

# Respuesta utilizada por la API

La API transforma la salida del modelo en un formato amigable.

Ejemplo:

```json
{
    "categoria":"Moderado",
    "probabilidad":0.95,
    "probabilitiesByClass":{
        "Eficiente":0.04,
        "Ineficiente":0.01,
        "Moderado":0.95
    },
    "recomendaciones":[
        "...",
        "..."
    ],
    "costoEstimadoMensual":183.2
}
```

---

# Validaciones

La API valida antes de ejecutar el modelo:

- `consumoKwh` > 0
- `cantidadEquipos` >= 1
- `horasAltoConsumo` entre 0 y 24
- `tipoInmueble` ∈ {Casa, Departamento}
- `usoHorarioPico` obligatorio
- los campos requeridos no pueden ser nulos

---

# Compatibilidad

Python:

- onnxruntime 1.23.2

Java:

```
com.microsoft.onnxruntime:onnxruntime:1.27.0
```

---

# Archivos entregados

```
models/
│
├── energy_efficiency_classifier_v1.onnx
├── energy_efficiency_pipeline_v1.joblib
├── model_contract_v1.json
└── SHA256SUMS.txt
```

---

# Garantías de consistencia

Se verificó la equivalencia entre:

- Pipeline de Scikit-learn
- Modelo ONNX

Resultados:

- 100% de coincidencia de etiquetas
- Diferencia máxima de probabilidades:
  1.11e-16

---

# Limitaciones

- El modelo utiliza pseudoetiquetas relativas.
- No corresponde a una certificación energética oficial.
- Su desempeño fue validado únicamente sobre el conjunto de datos del proyecto.