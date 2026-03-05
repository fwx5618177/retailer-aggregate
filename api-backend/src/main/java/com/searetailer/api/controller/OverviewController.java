package com.searetailer.api.controller;

import com.searetailer.api.model.dto.OverviewResponse;
import com.searetailer.api.service.OverviewService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDate;

@RestController
@RequestMapping("/api/v1")
@Tag(name = "Overview", description = "Dashboard overview data")
public class OverviewController {

    private final OverviewService overviewService;

    public OverviewController(OverviewService overviewService) {
        this.overviewService = overviewService;
    }

    @GetMapping("/overview")
    @Operation(summary = "Get overview dashboard data",
            description = "Returns aggregated KPIs, overlap statistics, price band distribution, and alerts summary.")
    public ResponseEntity<OverviewResponse> getOverview(
            @RequestParam(value = "category", defaultValue = "personal_care") String category,
            @RequestParam(value = "event_date", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate eventDate,
            @RequestParam(value = "window", defaultValue = "14d") String window) {

        OverviewResponse response = overviewService.getOverview(category, eventDate, window);
        return ResponseEntity.ok(response);
    }
}
