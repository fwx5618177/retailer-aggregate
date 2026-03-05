package com.searetailer.api.repository.clickhouse;

import com.searetailer.api.model.dto.ReviewQueueItemDto;
import com.searetailer.api.model.dto.TopItemDetailDto;
import com.searetailer.api.model.dto.TopItemDto;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@Repository
public class MatchMapClickHouseRepository {

    private static final Logger log = LoggerFactory.getLogger(MatchMapClickHouseRepository.class);

    private final JdbcTemplate clickHouseJdbcTemplate;

    public MatchMapClickHouseRepository(@Qualifier("clickHouseJdbcTemplate") JdbcTemplate clickHouseJdbcTemplate) {
        this.clickHouseJdbcTemplate = clickHouseJdbcTemplate;
    }

    /**
     * Find matches for a given item (works for both tiktok and shopee side).
     */
    public List<TopItemDetailDto.MatchResultDto> findMatchesForItem(String platform, String itemId) {
        String sql;
        if ("tiktok".equalsIgnoreCase(platform)) {
            sql = """
                SELECT m.tiktok_item_id, m.shopee_item_id, m.match_type, m.confidence, m.status,
                       m.reasons, m.rule_version,
                       tt.title AS tiktok_title, st.title AS shopee_title
                FROM match_map_platform m
                LEFT JOIN top_items tt ON m.tiktok_item_id = tt.item_id AND tt.platform = 'tiktok'
                LEFT JOIN top_items st ON m.shopee_item_id = st.item_id AND st.platform = 'shopee'
                WHERE m.tiktok_item_id = ?
                ORDER BY m.confidence DESC
                """;
        } else {
            sql = """
                SELECT m.tiktok_item_id, m.shopee_item_id, m.match_type, m.confidence, m.status,
                       m.reasons, m.rule_version,
                       tt.title AS tiktok_title, st.title AS shopee_title
                FROM match_map_platform m
                LEFT JOIN top_items tt ON m.tiktok_item_id = tt.item_id AND tt.platform = 'tiktok'
                LEFT JOIN top_items st ON m.shopee_item_id = st.item_id AND st.platform = 'shopee'
                WHERE m.shopee_item_id = ?
                ORDER BY m.confidence DESC
                """;
        }

        return clickHouseJdbcTemplate.query(sql, (rs, rowNum) -> TopItemDetailDto.MatchResultDto.builder()
                .tiktokItemId(rs.getString("tiktok_item_id"))
                .shopeeItemId(rs.getString("shopee_item_id"))
                .tiktokTitle(rs.getString("tiktok_title"))
                .shopeeTitle(rs.getString("shopee_title"))
                .matchType(rs.getString("match_type"))
                .confidence(rs.getDouble("confidence"))
                .status(rs.getString("status"))
                .reasons(rs.getString("reasons"))
                .ruleVersion(rs.getString("rule_version"))
                .build(), itemId);
    }

    /**
     * Find items in the review queue: matches with status = 'needs_review',
     * joined with top_items for both TikTok and Shopee side.
     *
     * DuckDB top_items does not have source_type; price comes from price_snapshots.
     */
    public List<ReviewQueueItemDto> findReviewQueue(String category, String sort, int limit, int offset) {
        String orderClause = switch (sort != null ? sort : "confidence_desc") {
            case "confidence_asc" -> "ORDER BY m.confidence ASC";
            case "date_desc" -> "ORDER BY tt.event_date DESC";
            default -> "ORDER BY m.confidence DESC";
        };

        StringBuilder sql = new StringBuilder("""
                SELECT
                    m.tiktok_item_id, m.shopee_item_id,
                    m.match_type, m.confidence, m.reasons, m.rule_version,
                    tt.event_date AS tt_event_date, tt.platform AS tt_platform, tt.item_id AS tt_item_id,
                    tt.title AS tt_title, tt.category AS tt_category, tt.rank AS tt_rank,
                    tt.url AS tt_url, tt.brand_raw AS tt_brand_raw, tt.brand_std AS tt_brand_std,
                    tt.size_value AS tt_size_value, tt.size_unit AS tt_size_unit,
                    tt.pack_count AS tt_pack_count, tt.image_url AS tt_image_url,
                    tp.price AS tt_price, tp.promo_price AS tt_promo_price, tp.currency AS tt_currency,
                    st.event_date AS st_event_date, st.platform AS st_platform, st.item_id AS st_item_id,
                    st.title AS st_title, st.category AS st_category, st.rank AS st_rank,
                    st.url AS st_url, st.brand_raw AS st_brand_raw, st.brand_std AS st_brand_std,
                    st.size_value AS st_size_value, st.size_unit AS st_size_unit,
                    st.pack_count AS st_pack_count, st.image_url AS st_image_url,
                    sp.price AS st_price, sp.promo_price AS st_promo_price, sp.currency AS st_currency
                FROM match_map_platform m
                INNER JOIN top_items tt ON m.tiktok_item_id = tt.item_id AND tt.platform = 'tiktok'
                INNER JOIN top_items st ON m.shopee_item_id = st.item_id AND st.platform = 'shopee'
                LEFT JOIN price_snapshots tp
                    ON tt.platform = tp.platform AND tt.item_id = tp.item_id AND tt.event_date = tp.event_date
                LEFT JOIN price_snapshots sp
                    ON st.platform = sp.platform AND st.item_id = sp.item_id AND st.event_date = sp.event_date
                WHERE m.status = 'needs_review'
                """);

        List<Object> params = new ArrayList<>();
        if (category != null && !category.isEmpty()) {
            sql.append(" AND tt.category = ?");
            params.add(category);
        }

        sql.append(" ").append(orderClause);
        sql.append(" LIMIT ? OFFSET ?");
        params.add(limit);
        params.add(offset);

        log.debug("Executing review queue query: {}", sql);
        return clickHouseJdbcTemplate.query(sql.toString(), (rs, rowNum) -> ReviewQueueItemDto.builder()
                .tiktokItemId(rs.getString("tiktok_item_id"))
                .shopeeItemId(rs.getString("shopee_item_id"))
                .matchType(rs.getString("match_type"))
                .confidence(rs.getDouble("confidence"))
                .reasons(rs.getString("reasons"))
                .ruleVersion(rs.getString("rule_version"))
                .tiktokItem(TopItemDto.builder()
                        .eventDate(rs.getObject("tt_event_date", LocalDate.class))
                        .platform(rs.getString("tt_platform"))
                        .itemId(rs.getString("tt_item_id"))
                        .title(rs.getString("tt_title"))
                        .category(rs.getString("tt_category"))
                        .rank(rs.getInt("tt_rank"))
                        .url(rs.getString("tt_url"))
                        .brandRaw(rs.getString("tt_brand_raw"))
                        .brandStd(rs.getString("tt_brand_std"))
                        .sizeValue(rs.getObject("tt_size_value") != null ? rs.getDouble("tt_size_value") : null)
                        .sizeUnit(rs.getString("tt_size_unit"))
                        .packCount(rs.getObject("tt_pack_count") != null ? rs.getInt("tt_pack_count") : null)
                        .imageUrl(rs.getString("tt_image_url"))
                        .listPrice(rs.getObject("tt_price") != null ? rs.getInt("tt_price") : null)
                        .promoPrice(rs.getObject("tt_promo_price") != null ? rs.getInt("tt_promo_price") : null)
                        .currency(rs.getString("tt_currency"))
                        .build())
                .shopeeItem(TopItemDto.builder()
                        .eventDate(rs.getObject("st_event_date", LocalDate.class))
                        .platform(rs.getString("st_platform"))
                        .itemId(rs.getString("st_item_id"))
                        .title(rs.getString("st_title"))
                        .category(rs.getString("st_category"))
                        .rank(rs.getInt("st_rank"))
                        .url(rs.getString("st_url"))
                        .brandRaw(rs.getString("st_brand_raw"))
                        .brandStd(rs.getString("st_brand_std"))
                        .sizeValue(rs.getObject("st_size_value") != null ? rs.getDouble("st_size_value") : null)
                        .sizeUnit(rs.getString("st_size_unit"))
                        .packCount(rs.getObject("st_pack_count") != null ? rs.getInt("st_pack_count") : null)
                        .imageUrl(rs.getString("st_image_url"))
                        .listPrice(rs.getObject("st_price") != null ? rs.getInt("st_price") : null)
                        .promoPrice(rs.getObject("st_promo_price") != null ? rs.getInt("st_promo_price") : null)
                        .currency(rs.getString("st_currency"))
                        .build())
                .build(), params.toArray());
    }

    /**
     * Count items in the review queue.
     */
    public long countReviewQueue(String category) {
        StringBuilder sql = new StringBuilder("""
                SELECT COUNT(*) FROM match_map_platform m
                INNER JOIN top_items tt ON m.tiktok_item_id = tt.item_id AND tt.platform = 'tiktok'
                WHERE m.status = 'needs_review'
                """);

        List<Object> params = new ArrayList<>();
        if (category != null && !category.isEmpty()) {
            sql.append(" AND tt.category = ?");
            params.add(category);
        }

        Long count = clickHouseJdbcTemplate.queryForObject(sql.toString(), Long.class, params.toArray());
        return count != null ? count : 0L;
    }

    /**
     * Get the current status of a match pair.
     */
    public String getMatchStatus(String tiktokItemId, String shopeeItemId) {
        String sql = """
                SELECT status FROM match_map_platform
                WHERE tiktok_item_id = ? AND shopee_item_id = ?
                LIMIT 1
                """;
        List<String> results = clickHouseJdbcTemplate.query(sql,
                (rs, rowNum) -> rs.getString("status"), tiktokItemId, shopeeItemId);
        return results.isEmpty() ? null : results.get(0);
    }
}
