package com.example.demo.dto;

import java.util.List;

public class CsvAnalysisResponse {

    private int totalRecords;
    private List<AnalisisResponse> results;

    public CsvAnalysisResponse() {
    }

    public CsvAnalysisResponse(int totalRecords, List<AnalisisResponse> results) {
        this.totalRecords = totalRecords;
        this.results = results;
    }

    public int getTotalRecords() {
        return totalRecords;
    }

    public void setTotalRecords(int totalRecords) {
        this.totalRecords = totalRecords;
    }

    public List<AnalisisResponse> getResults() {
        return results;
    }

    public void setResults(List<AnalisisResponse> results) {
        this.results = results;
    }
}
