package com.searetailer.api.controller;

import com.searetailer.api.model.dto.AlertDto;
import com.searetailer.api.model.dto.PagedResponse;
import com.searetailer.api.service.AlertsService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
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
@Tag(name = "Alerts", description = "Alerts and opportunities")
public class AlertsController {

    private final AlertsService alertsService;

    public AlertsController(AlertsService alertsService) {
        this.alertsService = alertsService;
    }

    @GetMapping("/alerts")
    @Operation(summary = "List alerts and opportunities",
            description = "Returns paginated list of alerts with optional filters.")
    public ResponseEntity<PagedResponse<AlertDto>> getAlerts(
            @RequestParam(value = "category", defaultValue = "personal_care") String category,

            @RequestParam(value = "event_date", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate eventDate,

            @RequestParam(value = "alert_type", required = false)
            @Parameter(description = "Filter by alert type: rank_jump, proxy_spike, platform_gap, price_anomaly")
            String alertType,

            @RequestParam(value = "severity", required = false)
            @Parameter(description = "Filter by severity: critical, high, medium, low")
            String severity,

            @RequestParam(value = "status", required = false)
            @Parameter(description = "Filter by status: open, acknowledged, resolved, dismissed")
            String status,

            @RequestParam(value = "limit", required = false) Integer limit,

            @RequestParam(value = "offset", required = false) Integer offset) {

        PagedResponse<AlertDto> response = alertsService.getAlerts(
                category, eventDate, alertType, severity, status, limit, offset);

        return ResponseEntity.ok(response);
    }
}
