package com.example.demo.controller;

import com.example.demo.dto.AnalisisResponse;
import com.example.demo.dto.CsvAnalysisResponse;
import com.example.demo.dto.ConsumoRequest;
import com.example.demo.exception.BadRequestException;
import com.example.demo.service.OnnxInferenceService;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;


@RestController
@RequestMapping("/api")
public class AnalisisController {

    private final OnnxInferenceService inferenceService;

    public AnalisisController(OnnxInferenceService inferenceService) {
        this.inferenceService = inferenceService;
    }

    /**
     * Endpoint JSON para enviar una sola petición al modelo ONNX.
     *
     * @param request Objeto JSON con los cinco campos del modelo.
     * @return Respuesta del modelo con categoría, probabilidad y recomendaciones.
     */
    @PostMapping(value = "/analisis-energetico", consumes = MediaType.APPLICATION_JSON_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
    public AnalisisResponse realizarAnalisis(@RequestBody ConsumoRequest request) {
        return inferenceService.predict(request);
    }

    /**
     * Endpoint CSV para enviar múltiples registros al modelo.
     * El archivo debe contener encabezados exactos.
     *
     * @param file Archivo CSV con las columnas: consumoKwh,usoHorarioPico,cantidadEquipos,tipoInmueble,horasAltoConsumo
     * @return Respuesta JSON con el total de registros procesados y lista de resultados.
     */
    @PostMapping(value = "/analisis-energetico/csv", consumes = MediaType.MULTIPART_FORM_DATA_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
    public CsvAnalysisResponse realizarAnalisisCsv(@RequestPart("file") MultipartFile file) {
        if (file.isEmpty()) {
            throw new BadRequestException("El archivo CSV no puede estar vacío.");
        }

        List<AnalisisResponse> responses = new ArrayList<>();

        try (BufferedReader reader = new BufferedReader(new InputStreamReader(file.getInputStream(), StandardCharsets.UTF_8))) {
            String headerLine = reader.readLine();
            if (headerLine == null) {
                throw new BadRequestException("El archivo CSV está vacío.");
            }

            String[] headers = headerLine.split(",");
            validateCsvHeader(headers);

            String line;
            int currentRow = 0;
            while ((line = reader.readLine()) != null) {
                currentRow++;
                if (line.trim().isEmpty()) {
                    continue;
                }

                ConsumoRequest request = parseCsvLine(line, currentRow);
                responses.add(inferenceService.predict(request));
            }
        } catch (IOException e) {
            throw new BadRequestException("No se pudo leer el archivo CSV: " + e.getMessage());
        }

        return new CsvAnalysisResponse(responses.size(), responses);
    }

    private void validateCsvHeader(String[] headers) {
        String[] expected = {"consumoKwh", "usoHorarioPico", "cantidadEquipos", "tipoInmueble", "horasAltoConsumo"};
        if (headers.length != expected.length) {
            throw new IllegalArgumentException("Encabezado CSV inválido. Se esperaban las columnas: " + String.join(",", expected));
        }

        for (int i = 0; i < expected.length; i++) {
            if (!headers[i].trim().equals(expected[i])) {
                throw new IllegalArgumentException("Encabezado CSV inválido en columna " + (i + 1) + ". Se esperaba '" + expected[i] + "'.");
            }
        }
    }

    private ConsumoRequest parseCsvLine(String line, int row) {
        String[] values = line.split(",");
        if (values.length != 5) {
            throw new IllegalArgumentException("La fila " + row + " no tiene 5 columnas válidas.");
        }

        try {
            return new ConsumoRequest(
                    Double.valueOf(values[0].trim()),
                    Boolean.valueOf(values[1].trim()),
                    Integer.valueOf(values[2].trim()),
                    values[3].trim(),
                    Integer.valueOf(values[4].trim())
            );
        } catch (NumberFormatException ex) {
            throw new IllegalArgumentException("Error de formato en la fila " + row + ": " + ex.getMessage(), ex);
        }
    }


}
