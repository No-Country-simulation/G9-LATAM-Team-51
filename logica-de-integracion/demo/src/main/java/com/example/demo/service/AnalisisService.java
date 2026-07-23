package com.example.demo.service;

import com.example.demo.dto.AnalisisResponse;
import com.example.demo.dto.ConsumoRequest;
import org.springframework.stereotype.Service;
import java.util.Arrays;

public class AnalisisService {
    public AnalisisResponse procesarConsumo(ConsumoRequest request) {

        // 1. Regla de Negocio: Cálculo de costo (tarifa $0.75)
        double costo = request.getConsumoKwh() * 0.75;

        // 2. Aqui Invocaremos al Modelo de IA real, cuando tengamos el Archivo.
        // x ahora mantenemos la respuesta simulada (Mock)
        String categoria = "Ineficiente";
        double probabilidad = 0.85;

        var recomendaciones = Arrays.asList(
                "Reducir el uso de equipos durante horarios pico",
                "Evaluar aparatos con alto consumo energético"
        );

        return new AnalisisResponse(
                categoria,
                probabilidad,
                recomendaciones,
                costo
        );
    }
}
