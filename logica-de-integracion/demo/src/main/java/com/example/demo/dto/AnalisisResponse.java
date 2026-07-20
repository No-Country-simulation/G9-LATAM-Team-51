package com.example.demo.dto;

import java.util.List;

public class AnalisisResponse {
    private String categoria;
    private Double probabilidad;
    private List<String> recomendaciones;
    private Double costoEstimadoMensual;

    public String getCategoria() {
        return categoria;
    }

    public void setCategoria(String categoria) {
        this.categoria = categoria;
    }

    public Double getProbabilidad() {
        return probabilidad;
    }

    public void setProbabilidad(Double probabilidad) {
        this.probabilidad = probabilidad;
    }

    public List<String> getRecomendaciones() {
        return recomendaciones;
    }

    public void setRecomendaciones(List<String> recomendaciones) {
        this.recomendaciones = recomendaciones;
    }

    public Double getCostoEstimadoMensual() {
        return costoEstimadoMensual;
    }

    public void setCostoEstimadoMensual(Double costoEstimadoMensual) {
        this.costoEstimadoMensual = costoEstimadoMensual;
    }

    public AnalisisResponse() {
    }

    public AnalisisResponse(String categoria, Double probabilidad, List<String> recomendaciones, Double costoEstimadoMensual) {
        this.categoria = categoria;
        this.probabilidad = probabilidad;
        this.recomendaciones = recomendaciones;
        this.costoEstimadoMensual = costoEstimadoMensual;
    }
}

