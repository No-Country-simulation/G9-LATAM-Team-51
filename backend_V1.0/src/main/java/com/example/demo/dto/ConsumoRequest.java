package com.example.demo.dto;

public record ConsumoRequest(
        Double consumoKwh,
        Boolean usoHorarioPico,
        Integer cantidadEquipos,
        String tipoInmueble,
        Integer horasAltoConsumo
) {}