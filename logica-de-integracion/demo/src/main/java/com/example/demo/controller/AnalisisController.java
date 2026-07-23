package com.example.demo.controller;

import com.example.demo.dto.AnalisisResponse;
import com.example.demo.dto.ConsumoRequest;
import org.springframework.web.bind.annotation.*;
import java.util.Arrays;
import com.example.demo.service.AnalisisService;

@RestController
@RequestMapping("/api")
public class AnalisisController {

    private final AnalisisService analisisService;

    public AnalisisController(AnalisisService analisisService) {
        this.analisisService = analisisService;
    }

    @PostMapping("/analisis-energetico")
    public AnalisisResponse realizarAnalisis(@RequestBody ConsumoRequest request) {
        return analisisService.procesarConsumo(request);
    }

}
