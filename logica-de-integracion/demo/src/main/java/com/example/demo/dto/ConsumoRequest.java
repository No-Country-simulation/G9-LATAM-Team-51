package com.example.demo.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class ConsumoRequest {
    @JsonProperty("consumo_kwh")
    private Double consumoKwh;

    @JsonProperty("uso_horario_pico")
    private Boolean usoHorarioPico;

    @JsonProperty("cantidad_equipos")
    private Integer cantidadEquipos;

    @JsonProperty("tipo_inmueble")
    private String tipoInmueble;

    @JsonProperty("horas_alto_consumo")
    private Integer horasAltoConsumo;

    public Double getConsumoKwh() {
        return consumoKwh;
    }

    public void setConsumoKwh(Double consumoKwh) {
        this.consumoKwh = consumoKwh;
    }

    public Boolean getUsoHorarioPico() {
        return usoHorarioPico;
    }

    public void setUsoHorarioPico(Boolean usoHorarioPico) {
        this.usoHorarioPico = usoHorarioPico;
    }

    public Integer getCantidadEquipos() {
        return cantidadEquipos;
    }

    public void setCantidadEquipos(Integer cantidadEquipos) {
        this.cantidadEquipos = cantidadEquipos;
    }

    public String getTipoInmueble() {
        return tipoInmueble;
    }

    public void setTipoInmueble(String tipoInmueble) {
        this.tipoInmueble = tipoInmueble;
    }

    public Integer getHorasAltoConsumo() {
        return horasAltoConsumo;
    }

    public void setHorasAltoConsumo(Integer horasAltoConsumo) {
        this.horasAltoConsumo = horasAltoConsumo;
    }
}

