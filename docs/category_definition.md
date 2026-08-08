# Category Definition Methodology

## Objetivo

Este documento describe la metodología utilizada para construir la variable objetivo (`categoria`) empleada durante el entrenamiento del modelo de Machine Learning.

Las categorías generadas representan niveles relativos de eficiencia energética dentro del conjunto de datos analizado y fueron diseñadas exclusivamente para fines académicos.

---

# Motivación

El conjunto de datos IDEAL proporciona mediciones de consumo energético, pero no incluye una etiqueta de eficiencia que pueda utilizarse directamente para entrenar un modelo de clasificación.

Por esta razón fue necesario construir una variable objetivo a partir de las características observadas en cada vivienda.

La metodología desarrollada recibe el nombre de:

```
ideal-relative-v1
```

---

# Variables consideradas

Para estimar el nivel relativo de eficiencia energética se utilizaron las siguientes variables:

| Variable | Descripción |
|-----------|-------------|
| consumo_kwh | Consumo mensual de energía |
| cantidad_equipos | Número de equipos eléctricos presentes |
| uso_horario_pico | Uso frecuente durante horarios de mayor demanda |
| horas_alto_consumo | Horas diarias de mayor consumo energético |
| tipo_inmueble | Tipo de vivienda |

Estas variables permiten describir el comportamiento energético de cada hogar.

---

# Construcción de la categoría

La metodología compara el consumo observado con el comportamiento esperado para viviendas con características similares.

En función de esa comparación se asigna una de tres categorías:

| Categoría | Interpretación |
|-----------|----------------|
| Eficiente | Consumo relativamente bajo para sus características |
| Moderado | Consumo cercano al comportamiento esperado |
| Ineficiente | Consumo relativamente alto para sus características |

No se utilizan umbrales fijos universales.

La clasificación depende de la distribución observada en el conjunto de datos.

---

# Naturaleza relativa

Las etiquetas obtenidas son relativas al dataset utilizado.

Esto significa que una vivienda clasificada como **Eficiente** en este proyecto no necesariamente recibiría la misma clasificación al compararse con otro conjunto de viviendas pertenecientes a otra ciudad, país o región.

Por esta razón las categorías no deben interpretarse como una certificación energética oficial.

---

# Metodología utilizada

El proceso general seguido para generar las etiquetas fue:

```
Datos limpios
        │
        ▼
Agregación mensual
        │
        ▼
Construcción de variables
        │
        ▼
Comparación relativa
        │
        ▼
Asignación de categoría
```

---

# Distribución de categorías

El conjunto final contiene tres clases balanceadas para permitir el entrenamiento de un modelo supervisado.

Las categorías utilizadas fueron:

- Eficiente
- Moderado
- Ineficiente

---

# Uso durante el entrenamiento

La columna objetivo utilizada por los modelos fue:

```
categoria
```

Todas las evaluaciones, métricas y validaciones fueron realizadas utilizando esta variable como etiqueta de referencia.

---

# Relación con el modelo

El modelo de Machine Learning no aprende reglas definidas manualmente.

Durante el entrenamiento aprende patrones presentes en las categorías generadas mediante la metodología `ideal-relative-v1`.

Una vez entrenado, el modelo puede estimar la categoría correspondiente para nuevos registros utilizando únicamente las variables de entrada.

---

# Limitaciones

La metodología presenta las siguientes limitaciones:

- las categorías son relativas al conjunto de datos utilizado;
- no representan certificaciones energéticas oficiales;
- los resultados dependen de la calidad de los datos disponibles;
- la aplicación en otros contextos requiere un proceso de validación adicional.

---

# Trabajo futuro

Como línea futura de investigación se propone:

- incorporar indicadores climáticos;
- considerar características constructivas de las viviendas;
- incluir información socioeconómica cuando esté disponible;
- comparar esta metodología con estándares internacionales de eficiencia energética.