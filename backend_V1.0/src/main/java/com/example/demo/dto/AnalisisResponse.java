package com.example.demo.dto;

import java.util.List;
import java.util.Map;

public record AnalisisResponse(
        String categoria,
        Double probabilidad,
        Map<String, Double> probabilitiesByClass,
        List<String> recomendaciones,
        Double costoEstimadoMensual
) {}