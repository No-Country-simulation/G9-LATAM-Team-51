package com.example.demo.controller;

import com.example.demo.dto.AnalisisResponse;
import com.example.demo.dto.ConsumoRequest;
import org.springframework.web.bind.annotation.*;
import java.util.Arrays;

@RestController
@RequestMapping("/api")
public class AnalisisController {

    @PostMapping("/analisis-energetico")
    public AnalisisResponse realizarAnalisis(@RequestBody ConsumoRequest request) {

        // 1. Lógica dura: Calcular el costo estimado (tarifa fija de R$ 0,75)
        double costo = request.getConsumoKwh() * 0.75;

        // 2. Mock temporal (simulación): Devolvemos datos fijos
        // mientras los Data Scientists terminan el modelo de IA
        String categoriaSimulada = "Ineficiente";
        double probabilidadSimulada = 0.85;

        var recomendacionesSimuladas = Arrays.asList(
                "Reducir el uso de equipos durante horarios pico",
                "Evaluar aparatos con alto consumo energético"
        );

        // 3. Retornar la respuesta estructurada
        return new AnalisisResponse(
                categoriaSimulada,
                probabilidadSimulada,
                recomendacionesSimuladas,
                costo
        );
    }

}
