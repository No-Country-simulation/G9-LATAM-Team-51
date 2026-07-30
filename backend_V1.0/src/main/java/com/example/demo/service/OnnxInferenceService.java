package com.example.demo.service;

import com.example.demo.dto.AnalisisResponse;
import com.example.demo.dto.ConsumoRequest;
import com.example.demo.exception.BadRequestException;
import ai.onnxruntime.OnnxTensor;
import ai.onnxruntime.OrtEnvironment;
import ai.onnxruntime.OrtException;
import ai.onnxruntime.OrtSession;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.core.io.ClassPathResource;

import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class OnnxInferenceService implements AutoCloseable {

    private static final List<String> CLASS_ORDER = List.of("Eficiente", "Ineficiente", "Moderado");
    private static final Map<String, Integer> CLASS_INDEX = Map.of(
            "Eficiente", 0,
            "Ineficiente", 1,
            "Moderado", 2
    );

    private final OrtEnvironment environment;
    private final OrtSession session;

    public OnnxInferenceService(@Value("${model.path}") String modelPath) {
        try {
            this.environment = OrtEnvironment.getEnvironment();
            // Lee el archivo directamente desde el classpath (resources)
            byte[] modelBytes = new ClassPathResource(modelPath).getInputStream().readAllBytes();
            this.session = environment.createSession(modelBytes, new OrtSession.SessionOptions());
        } catch (OrtException | IOException e) {
            throw new IllegalStateException("No se pudo cargar el modelo ONNX desde: " + modelPath, e);
        }
    }

    /**
     * Ejecuta la inferencia ONNX para una sola petición JSON.
     *
     * @param request Petición del cliente con los cinco campos requeridos.
     * @return Respuesta con categoría, probabilidad, recomendaciones y costo.
     */
    public AnalisisResponse predict(ConsumoRequest request) {
        validateRequest(request);

        double costoCalculado = request.consumoKwh() * 0.75;
        double costoEstimadoMensual = redondear(costoCalculado, 2);

        try (
                OnnxTensor consumoTensor = OnnxTensor.createTensor(environment, new double[][]{{request.consumoKwh()}});
                OnnxTensor usoHorarioPicoTensor = OnnxTensor.createTensor(environment, new long[][]{{request.usoHorarioPico() ? 1L : 0L}});
                OnnxTensor cantidadEquiposTensor = OnnxTensor.createTensor(environment, new long[][]{{request.cantidadEquipos().longValue()}});
                OnnxTensor tipoInmuebleTensor = OnnxTensor.createTensor(environment, new String[][]{{request.tipoInmueble()}});
                OnnxTensor horasAltoConsumoTensor = OnnxTensor.createTensor(environment, new long[][]{{request.horasAltoConsumo().longValue()}})
        ) {
            Map<String, OnnxTensor> inputs = Map.of(
                    "consumo_kwh", consumoTensor,
                    "uso_horario_pico", usoHorarioPicoTensor,
                    "cantidad_equipos", cantidadEquiposTensor,
                    "tipo_inmueble", tipoInmuebleTensor,
                    "horas_alto_consumo", horasAltoConsumoTensor
            );

            try (OrtSession.Result result = session.run(inputs)) {
                String[] labels = (String[]) result.get("label")
                        .orElseThrow(() -> new IllegalStateException("Salida ONNX 'label' no encontrada"))
                        .getValue();
                double[][] probabilities = (double[][]) result.get("probabilities")
                        .orElseThrow(() -> new IllegalStateException("Salida ONNX 'probabilities' no encontrada"))
                        .getValue();

                String categoria = labels[0];
                Integer classIndex = CLASS_INDEX.get(categoria);
                if (classIndex == null) {
                    throw new IllegalStateException("Categoría desconocida devuelta por el modelo: " + categoria);
                }

                Map<String, Double> probabilidadesPorClase = new LinkedHashMap<>();
                for (String clase : CLASS_ORDER) {
                    int index = CLASS_INDEX.get(clase);
                    probabilidadesPorClase.put(clase, redondear(probabilities[0][index], 4));
                }

                double probabilidad = redondear(probabilities[0][classIndex], 4);
                List<String> recomendaciones = generarRecomendaciones(categoria);

                return new AnalisisResponse(categoria, probabilidad, probabilidadesPorClase, recomendaciones, costoEstimadoMensual);
            }
        } catch (OrtException e) {
            throw new IllegalStateException("Error ejecutando la inferencia ONNX", e);
        }
    }

    private void validateRequest(ConsumoRequest request) {
        if (request == null) {
            throw new BadRequestException("La petición no puede ser nula.");
        }
        if (request.consumoKwh() == null || request.consumoKwh() <= 0) {
            throw new BadRequestException("El campo consumoKwh es obligatorio y debe ser mayor a 0.");
        }
        if (request.usoHorarioPico() == null) {
            throw new BadRequestException("El campo usoHorarioPico es obligatorio.");
        }
        if (request.cantidadEquipos() == null || request.cantidadEquipos() < 1) {
            throw new BadRequestException("El campo cantidadEquipos es obligatorio y debe ser al menos 1.");
        }
        if (request.tipoInmueble() == null || !(request.tipoInmueble().equals("Casa") || request.tipoInmueble().equals("Departamento"))) {
            throw new BadRequestException("El campo tipoInmueble es obligatorio y debe ser 'Casa' o 'Departamento'.");
        }
        if (request.horasAltoConsumo() == null || request.horasAltoConsumo() < 0 || request.horasAltoConsumo() > 24) {
            throw new BadRequestException("El campo horasAltoConsumo es obligatorio y debe estar entre 0 y 24.");
        }
    }

    private List<String> generarRecomendaciones(String categoria) {
        if ("Eficiente".equals(categoria)) {
            return List.of(
                    "Mantener las prácticas actuales de consumo.",
                    "Revisar si es posible optimizar más con equipos eficientes."
            );
        }
        if ("Moderado".equals(categoria)) {
            return List.of(
                    "Reducir el uso de equipos durante horarios pico.",
                    "Monitorear el consumo para identificar patrones de mejora."
            );
        }
        return List.of(
                "Reducir el uso de equipos durante horarios pico.",
                "Evaluar aparatos con alto consumo energético."
        );
    }

    @Override
    public void close() throws Exception {
        session.close();
        environment.close();
    }

    private double redondear(double valor, int decimales){
        return BigDecimal.valueOf(valor)
                .setScale(decimales, RoundingMode.HALF_UP)
                .doubleValue();
    }
}
