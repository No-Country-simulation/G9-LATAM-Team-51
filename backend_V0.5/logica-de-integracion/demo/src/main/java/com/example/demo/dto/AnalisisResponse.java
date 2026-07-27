package com.example.demo.dto;

import java.util.List;
import java.util.Map;

public class AnalisisResponse {
    private String categoria;
    private Double probabilidad;
    private Map<String, Double> probabilitiesByClass;
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

    public Map<String, Double> getProbabilitiesByClass() {
        return probabilitiesByClass;
    }

    public void setProbabilitiesByClass(Map<String, Double> probabilitiesByClass) {
        this.probabilitiesByClass = probabilitiesByClass;
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

    public AnalisisResponse(String categoria, Double probabilidad, Map<String, Double> probabilitiesByClass, List<String> recomendaciones, Double costoEstimadoMensual) {
        this.categoria = categoria;
        this.probabilidad = probabilidad;
        this.probabilitiesByClass = probabilitiesByClass;
        this.recomendaciones = recomendaciones;
        this.costoEstimadoMensual = costoEstimadoMensual;
    }
}

