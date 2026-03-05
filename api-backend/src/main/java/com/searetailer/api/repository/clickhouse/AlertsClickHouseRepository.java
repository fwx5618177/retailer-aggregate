package com.searetailer.api.repository.clickhouse;

import com.searetailer.api.model.dto.AlertDto;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@Repository
public class AlertsClickHouseRepository {

    private static final Logger log = LoggerFactory.getLogger(AlertsClickHouseRepository.class);

    private final JdbcTemplate clickHouseJdbcTemplate;

    public AlertsClickHouseRepository(@Qualifier("clickHouseJdbcTemplate") JdbcTemplate clickHouseJdbcTemplate) {
        this.clickHouseJdbcTemplate = clickHouseJdbcTemplate;
    }

    /**
     * Find alerts with filters and pagination.
     *
     * DuckDB alerts schema: alert_id, event_date, platform, item_id (single),
     * alert_type, severity, status, message, details, suggested_action, run_id, created_at.
     *
     * The DTO maps: item_id → itemIds (single-element list), message → title, details → description.
     */
    public List<AlertDto> findAlerts(String category, LocalDate eventDate, String alertType,
                                      String severity, String status, int limit, int offset) {
        StringBuilder sql = new StringBuilder("""
                SELECT alert_id, event_date, platform, item_id, alert_type, severity,
                       status, message, details, suggested_action
                FROM alerts
                WHERE 1=1
                """);

        List<Object> params = new ArrayList<>();

        if (eventDate != null) {
            sql.append(" AND event_date = ?");
            params.add(eventDate);
        }
        if (alertType != null && !alertType.isEmpty()) {
            sql.append(" AND alert_type = ?");
            params.add(alertType);
        }
        if (severity != null && !severity.isEmpty()) {
            sql.append(" AND severity = ?");
            params.add(severity);
        }
        if (status != null && !status.isEmpty()) {
            sql.append(" AND status = ?");
            params.add(status);
        }

        sql.append(" ORDER BY event_date DESC, severity ASC");
        sql.append(" LIMIT ? OFFSET ?");
        params.add(limit);
        params.add(offset);

        log.debug("Executing alerts query: {}", sql);
        return clickHouseJdbcTemplate.query(sql.toString(), (rs, rowNum) -> {
            String itemId = rs.getString("item_id");
            List<String> itemIds = itemId != null ? List.of(itemId) : List.of();

            return AlertDto.builder()
                    .alertId(rs.getString("alert_id"))
                    .eventDate(rs.getObject("event_date", LocalDate.class))
                    .platform(rs.getString("platform"))
                    .itemIds(itemIds)
                    .alertType(rs.getString("alert_type"))
                    .severity(rs.getString("severity"))
                    .status(rs.getString("status"))
                    .title(rs.getString("message"))
                    .description(rs.getString("details"))
                    .suggestedAction(rs.getString("suggested_action"))
                    .build();
        }, params.toArray());
    }

    /**
     * Count alerts matching filters.
     */
    public long countAlerts(String category, LocalDate eventDate, String alertType,
                            String severity, String status) {
        StringBuilder sql = new StringBuilder("SELECT COUNT(*) FROM alerts WHERE 1=1");
        List<Object> params = new ArrayList<>();

        if (eventDate != null) {
            sql.append(" AND event_date = ?");
            params.add(eventDate);
        }
        if (alertType != null && !alertType.isEmpty()) {
            sql.append(" AND alert_type = ?");
            params.add(alertType);
        }
        if (severity != null && !severity.isEmpty()) {
            sql.append(" AND severity = ?");
            params.add(severity);
        }
        if (status != null && !status.isEmpty()) {
            sql.append(" AND status = ?");
            params.add(status);
        }

        Long count = clickHouseJdbcTemplate.queryForObject(sql.toString(), Long.class, params.toArray());
        return count != null ? count : 0L;
    }
}
