package com.searetailer.api.repository.clickhouse;

import com.searetailer.api.model.dto.OverviewResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Repository
public class OverviewClickHouseRepository {

    private static final Logger log = LoggerFactory.getLogger(OverviewClickHouseRepository.class);

    private final JdbcTemplate clickHouseJdbcTemplate;

    public OverviewClickHouseRepository(@Qualifier("clickHouseJdbcTemplate") JdbcTemplate clickHouseJdbcTemplate) {
        this.clickHouseJdbcTemplate = clickHouseJdbcTemplate;
    }

    /**
     * Count total items per platform for a category and event date.
     */
    public OverviewResponse.TotalItems getTotalItems(String category, LocalDate eventDate) {
        String sql = """
                SELECT platform, COUNT(*) AS cnt
                FROM top_items
                WHERE category = ? AND event_date = ?
                GROUP BY platform
                """;

        Map<String, Integer> counts = new HashMap<>();
        clickHouseJdbcTemplate.query(sql, rs -> {
            counts.put(rs.getString("platform"), rs.getInt("cnt"));
        }, category, eventDate);

        return OverviewResponse.TotalItems.builder()
                .tiktok(counts.getOrDefault("tiktok", 0))
                .shopee(counts.getOrDefault("shopee", 0))
                .build();
    }

    /**
     * Count overlap by match type from match_map_platform.
     */
    public OverviewResponse.Overlap getOverlap(String category, LocalDate eventDate) {
        String sql = """
                SELECT m.match_type, COUNT(*) AS cnt
                FROM match_map_platform m
                INNER JOIN top_items t ON m.tiktok_item_id = t.item_id AND t.platform = 'tiktok'
                WHERE t.category = ? AND t.event_date = ?
                  AND m.status != 'no_match'
                GROUP BY m.match_type
                """;

        Map<String, Integer> matchCounts = new HashMap<>();
        clickHouseJdbcTemplate.query(sql, rs -> {
            matchCounts.put(rs.getString("match_type"), rs.getInt("cnt"));
        }, category, eventDate);

        int exactSame = matchCounts.getOrDefault("exact_same", 0);
        int variantFamily = matchCounts.getOrDefault("variant_family", 0);
        int similar = matchCounts.getOrDefault("similar", 0);
        int totalMatched = exactSame + variantFamily + similar;

        return OverviewResponse.Overlap.builder()
                .exactSame(exactSame)
                .variantFamily(variantFamily)
                .similar(similar)
                .totalMatched(totalMatched)
                .build();
    }

    /**
     * Count items needing review.
     */
    public int getNeedsReviewCount(String category, LocalDate eventDate) {
        String sql = """
                SELECT COUNT(*) AS cnt
                FROM match_map_platform m
                INNER JOIN top_items t ON m.tiktok_item_id = t.item_id AND t.platform = 'tiktok'
                WHERE t.category = ? AND t.event_date = ?
                  AND m.status = 'needs_review'
                """;

        Integer count = clickHouseJdbcTemplate.queryForObject(sql, Integer.class, category, eventDate);
        return count != null ? count : 0;
    }

    /**
     * Get price band distribution for both platforms.
     * Uses ANSI CASE WHEN instead of ClickHouse multiIf/countIf.
     * Price is in the price_snapshots table (satang units).
     */
    public List<OverviewResponse.PriceBandEntry> getPriceBandDistribution(String category, LocalDate eventDate) {
        String sql = """
                SELECT
                    CASE
                        WHEN p.price < 10000 THEN 'Under 100'
                        WHEN p.price < 30000 THEN '100-299'
                        WHEN p.price < 50000 THEN '300-499'
                        WHEN p.price < 100000 THEN '500-999'
                        ELSE '1000+'
                    END AS band,
                    COUNT(CASE WHEN t.platform = 'tiktok' THEN 1 END) AS tiktok_count,
                    COUNT(CASE WHEN t.platform = 'shopee' THEN 1 END) AS shopee_count
                FROM top_items t
                INNER JOIN price_snapshots p
                    ON t.platform = p.platform AND t.item_id = p.item_id AND t.event_date = p.event_date
                WHERE t.category = ? AND t.event_date = ?
                GROUP BY band
                ORDER BY
                    CASE band
                        WHEN 'Under 100' THEN 1
                        WHEN '100-299' THEN 2
                        WHEN '300-499' THEN 3
                        WHEN '500-999' THEN 4
                        ELSE 5
                    END
                """;

        return clickHouseJdbcTemplate.query(sql, (rs, rowNum) -> OverviewResponse.PriceBandEntry.builder()
                .band(rs.getString("band"))
                .tiktokCount(rs.getInt("tiktok_count"))
                .shopeeCount(rs.getInt("shopee_count"))
                .build(), category, eventDate);
    }

    /**
     * Get top brands across both platforms.
     */
    public List<OverviewResponse.TopBrandEntry> getTopBrands(String category, LocalDate eventDate, int topN) {
        String sql = """
                SELECT
                    COALESCE(brand_std, brand_raw, 'Unknown') AS brand,
                    COUNT(CASE WHEN platform = 'tiktok' THEN 1 END) AS tiktok_count,
                    COUNT(CASE WHEN platform = 'shopee' THEN 1 END) AS shopee_count
                FROM top_items
                WHERE category = ? AND event_date = ?
                  AND brand_std IS NOT NULL AND brand_std != ''
                GROUP BY brand
                ORDER BY (COUNT(CASE WHEN platform = 'tiktok' THEN 1 END)
                        + COUNT(CASE WHEN platform = 'shopee' THEN 1 END)) DESC
                LIMIT ?
                """;

        return clickHouseJdbcTemplate.query(sql, (rs, rowNum) -> OverviewResponse.TopBrandEntry.builder()
                .brand(rs.getString("brand"))
                .tiktokCount(rs.getInt("tiktok_count"))
                .shopeeCount(rs.getInt("shopee_count"))
                .build(), category, eventDate, topN);
    }

    /**
     * Get alerts summary (counts by severity and type).
     */
    public OverviewResponse.AlertsSummary getAlertsSummary(String category, LocalDate eventDate) {
        String totalSql = "SELECT COUNT(*) AS cnt FROM alerts WHERE event_date = ?";

        String bySeveritySql = """
                SELECT severity, COUNT(*) AS cnt FROM alerts
                WHERE event_date = ?
                GROUP BY severity
                """;

        String byTypeSql = """
                SELECT alert_type, COUNT(*) AS cnt FROM alerts
                WHERE event_date = ?
                GROUP BY alert_type
                """;

        Integer total = clickHouseJdbcTemplate.queryForObject(totalSql, Integer.class, eventDate);

        Map<String, Integer> bySeverity = new HashMap<>();
        clickHouseJdbcTemplate.query(bySeveritySql, rs -> {
            bySeverity.put(rs.getString("severity"), rs.getInt("cnt"));
        }, eventDate);

        Map<String, Integer> byType = new HashMap<>();
        clickHouseJdbcTemplate.query(byTypeSql, rs -> {
            byType.put(rs.getString("alert_type"), rs.getInt("cnt"));
        }, eventDate);

        return OverviewResponse.AlertsSummary.builder()
                .total(total != null ? total : 0)
                .bySeverity(bySeverity)
                .byType(byType)
                .build();
    }

    /**
     * Get the latest batch metadata for a category and event date.
     */
    public OverviewResponse.Metadata getMetadata(String category, LocalDate eventDate) {
        String sql = """
                SELECT batch_id
                FROM top_items
                WHERE category = ? AND event_date = ?
                LIMIT 1
                """;

        List<OverviewResponse.Metadata> results = clickHouseJdbcTemplate.query(sql, (rs, rowNum) ->
                OverviewResponse.Metadata.builder()
                        .batchId(rs.getString("batch_id"))
                        .build(), category, eventDate);

        if (results.isEmpty()) {
            return OverviewResponse.Metadata.builder().build();
        }

        OverviewResponse.Metadata meta = results.get(0);

        // Get rule_version + schema_version from match_map_platform
        String ruleVersionSql = """
                SELECT rule_version, schema_version FROM match_map_platform
                ORDER BY ingested_at DESC
                LIMIT 1
                """;
        List<Map<String, String>> versions = clickHouseJdbcTemplate.query(ruleVersionSql,
                (rs, rowNum) -> {
                    Map<String, String> m = new HashMap<>();
                    m.put("rule_version", rs.getString("rule_version"));
                    m.put("schema_version", rs.getString("schema_version"));
                    return m;
                });

        if (!versions.isEmpty()) {
            meta.setRuleVersion(versions.get(0).get("rule_version"));
            meta.setSchemaVersion(versions.get(0).get("schema_version"));
        }

        return meta;
    }
}
