package com.searetailer.api.service;

import com.searetailer.api.model.dto.AlertDto;
import com.searetailer.api.model.dto.PagedResponse;
import com.searetailer.api.repository.clickhouse.AlertsClickHouseRepository;
import com.searetailer.api.util.PaginationUtil;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;

@Service
public class AlertsService {

    private static final Logger log = LoggerFactory.getLogger(AlertsService.class);

    private final AlertsClickHouseRepository alertsRepo;
    private final PaginationUtil paginationUtil;

    public AlertsService(AlertsClickHouseRepository alertsRepo, PaginationUtil paginationUtil) {
        this.alertsRepo = alertsRepo;
        this.paginationUtil = paginationUtil;
    }

    /**
     * Get paginated alerts with filters.
     */
    public PagedResponse<AlertDto> getAlerts(String category, LocalDate eventDate, String alertType,
                                               String severity, String status, Integer limit, Integer offset) {
        int validatedLimit = paginationUtil.validateLimit(limit);
        int validatedOffset = paginationUtil.validateOffset(offset);

        log.info("Fetching alerts: category={}, eventDate={}, alertType={}, severity={}, status={}",
                category, eventDate, alertType, severity, status);

        List<AlertDto> alerts = alertsRepo.findAlerts(
                category, eventDate, alertType, severity, status, validatedLimit, validatedOffset);

        long total = alertsRepo.countAlerts(category, eventDate, alertType, severity, status);

        return paginationUtil.buildPagedResponse(alerts, total, validatedLimit, validatedOffset);
    }
}
