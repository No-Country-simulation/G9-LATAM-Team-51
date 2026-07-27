# Handoff del modelo ONNX a Back-End

**Proveedor:** equipo de Datos — Tomás Maldonado

**Consumidor:** API Java/Spring Boot

**Modelo:** `energy_efficiency_classifier_v1.onnx`

**Versión:** `1.0.0`

## División de responsabilidades

Datos:

1. Entrena el modelo en Python.
2. Exporta el pipeline de inferencia a ONNX.
3. Define entradas, salidas y orden de clases.
4. Comprueba la paridad Python↔ONNX.
5. Entrega ejemplos esperados y hashes.

Back-End:

1. Incluye ONNX Runtime en Maven.
2. Empaqueta o carga el archivo `.onnx`.
3. Convierte el DTO REST a los cinco tensores.
4. Ejecuta la sesión ONNX.
5. Mapea `label` y `probabilities` a `AnalisisResponse`.
6. Ejecuta los tres casos de aceptación entregados.

DevOps:

1. Configura el artefacto o imagen desplegable.
2. Gestiona OCI, variables y observabilidad.

## Artefacto que debe usar Java

```text
models/energy_efficiency_classifier_v1.onnx
```

`energy_efficiency_pipeline_v1.joblib` es únicamente un respaldo Python. Java
no debe intentar abrirlo.

Antes de integrar, comprobar el SHA-256 indicado en
`models/SHA256SUMS.txt`.

## Dependencia Maven

Añadir al `pom.xml` del Back-End:

```xml
<dependency>
    <groupId>com.microsoft.onnxruntime</groupId>
    <artifactId>onnxruntime</artifactId>
    <version>1.27.0</version>
</dependency>
```

No se necesita PMML ni `pmml-evaluator` para este modelo.

## Mapeo del DTO a ONNX

Cada petición individual usa forma `[1, 1]`:

| Campo del DTO | Entrada ONNX | Tipo ONNX | Conversión |
| --- | --- | --- | --- |
| `consumoKwh` | `consumo_kwh` | `DOUBLE` | `double[][]` |
| `usoHorarioPico` | `uso_horario_pico` | `INT64` | `true→1L`, `false→0L` |
| `cantidadEquipos` | `cantidad_equipos` | `INT64` | `long[][]` |
| `tipoInmueble` | `tipo_inmueble` | `STRING` | `String[][]` |
| `horasAltoConsumo` | `horas_alto_consumo` | `INT64` | `long[][]` |

Validaciones mínimas antes de inferencia:

- Los cinco campos son obligatorios.
- `consumoKwh > 0`.
- `cantidadEquipos >= 1`.
- `tipoInmueble` es exactamente `Casa` o `Departamento`.
- `horasAltoConsumo` es entero entre 0 y 24.

## Salidas

El modelo devuelve:

- `label`: arreglo `String[]` con la categoría predicha.
- `probabilities`: matriz `double[][]` con tres probabilidades.

El orden exacto de las probabilidades es:

```text
índice 0 = Eficiente
índice 1 = Ineficiente
índice 2 = Moderado
```

Este orden no debe cambiarse por el orden visual de los reportes.

## Esqueleto de inferencia Java

El código definitivo puede organizarse como un servicio singleton que abre la
sesión una sola vez al iniciar Spring:

```java
OrtEnvironment env = OrtEnvironment.getEnvironment();
OrtSession.SessionOptions options = new OrtSession.SessionOptions();
OrtSession session = env.createSession(modelPath, options);

try (
    OnnxTensor consumo = OnnxTensor.createTensor(
        env, new double[][] {{ request.getConsumoKwh() }}
    );
    OnnxTensor pico = OnnxTensor.createTensor(
        env, new long[][] {{ request.getUsoHorarioPico() ? 1L : 0L }}
    );
    OnnxTensor equipos = OnnxTensor.createTensor(
        env, new long[][] {{ request.getCantidadEquipos().longValue() }}
    );
    OnnxTensor inmueble = OnnxTensor.createTensor(
        env, new String[][] {{ request.getTipoInmueble() }}
    );
    OnnxTensor horas = OnnxTensor.createTensor(
        env, new long[][] {{ request.getHorasAltoConsumo().longValue() }}
    )
) {
    Map<String, OnnxTensor> inputs = Map.of(
        "consumo_kwh", consumo,
        "uso_horario_pico", pico,
        "cantidad_equipos", equipos,
        "tipo_inmueble", inmueble,
        "horas_alto_consumo", horas
    );

    try (OrtSession.Result result = session.run(inputs)) {
        String[] labels = (String[]) result.get("label")
            .orElseThrow()
            .getValue();
        double[][] probabilities = (double[][]) result.get("probabilities")
            .orElseThrow()
            .getValue();

        String categoria = labels[0];
        int classIndex = switch (categoria) {
            case "Eficiente" -> 0;
            case "Ineficiente" -> 1;
            case "Moderado" -> 2;
            default -> throw new IllegalStateException("Categoría desconocida");
        };
        double probabilidad = probabilities[0][classIndex];
    }
}
```

La sesión y el entorno deben cerrarse al apagar la aplicación; los tensores y
el resultado deben cerrarse en cada petición.

## Pruebas de aceptación

Back-End debe ejecutar los tres casos de
`reports/onnx_prediction_examples.json` y comprobar:

1. La categoría coincide exactamente.
2. La probabilidad coincide con tolerancia `1e-9`.
3. Las tres probabilidades suman aproximadamente `1.0`.
4. Una petición inválida devuelve `400`, no un error interno `500`.

## Evidencia de Datos

`reports/onnx_parity_report.json` registra:

- 555 de 555 etiquetas coincidentes.
- Diferencia máxima de probabilidad: `2.220446049250313e-16`.
- Accuracy de test ONNX: `0.9435483870967742`.
- F1 macro de test ONNX: `0.9441585632874531`.
