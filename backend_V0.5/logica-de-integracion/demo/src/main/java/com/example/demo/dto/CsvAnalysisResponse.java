package com.example.demo.dto;

import java.util.List;

public record CsvAnalysisResponse(
        int totalRecords,
        List<AnalisisResponse> results
) {}