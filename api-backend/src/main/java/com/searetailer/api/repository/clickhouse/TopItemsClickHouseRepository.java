package com.searetailer.api.repository.clickhouse;

import com.searetailer.api.model.dto.TopItemDto;
import com.searetailer.api.model.dto.TopItemDetailDto;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@Repository
public class TopItemsClickHouseRepository {

    private static final Logger log = LoggerFactory.getLogger(TopItemsClickHouseRepository.class);

    private final JdbcTemplate clickHouseJdbcTemplate;

    public TopItemsClickHouseRepository(@Qualifier("clickHouseJdbcTemplate") JdbcTemplate clickHouseJdbcTemplate) {
        this.clickHouseJdbcTemplate = clickHouseJdbcTemplate;
    }

    /**
     * Row mapper for top_items joined with price_snapshots.
     * Handles nullable columns gracefully.
     */
    private static final RowMapper<TopItemDto> TOP_ITEM_ROW_MAPPER = (rs, rowNum) -> TopItemDto.builder()
            .eventDate(rs.getObject("event_date", LocalDate.class))
            .platform(rs.getString("platform"))
            .itemId(rs.getString("item_id"))
            .title(rs.getString("title"))
            .category(rs.getString("category"))
            .rank(rs.getInt("rank"))
            .url(rs.getString("url"))
            .brandRaw(rs.getString("brand_raw"))
            .brandStd(rs.getString("brand_std"))
            .sizeValue(rs.getObject("size_value") != null ? rs.getDouble("size_value") : null)
            .sizeUnit(rs.getString("size_unit"))
            .packCount(rs.getObject("pack_count") != null ? rs.getInt("pack_count") : null)
            .imageUrl(rs.getString("image_url"))
            .listPrice(rs.getObject("price") != null ? rs.getInt("price") : null)
            .promoPrice(rs.getObject("promo_price") != null ? rs.getInt("promo_price") : null)
            .currency(rs.getString("currency"))
            .build();

    private static final String BASE_SELECT = """
            SELECT t.event_date, t.platform, t.item_id, t.title, t.category, t.rank, t.url,
                   t.brand_raw, t.brand_std, t.size_value, t.size_unit, t.pack_count, t.image_url,
                   p.price, p.promo_price, p.currency
            FROM top_items t
            LEFT JOIN price_snapshots p
                ON t.platform = p.platform AND t.item_id = p.item_id AND t.event_date = p.event_date
            """;

    /**
     * Find top items with filters, pagination, and sorting.
     */
    public List<TopItemDto> findTopItems(String platform, String category, LocalDate eventDate,
                                          String brand, Integer priceMin, Integer priceMax,
                                          String sort, int limit, int offset) {
        StringBuilder sql = new StringBuilder(BASE_SELECT + " WHERE 1=1");
        List<Object> params = new ArrayList<>();

        if (platform != null && !platform.isEmpty()) {
            sql.append(" AND t.platform = ?");
            params.add(platform);
        }
        if (category != null && !category.isEmpty()) {
            sql.append(" AND t.category = ?");
            params.add(category);
        }
        if (eventDate != null) {
            sql.append(" AND t.event_date = ?");
            params.add(eventDate);
        }
        if (brand != null && !brand.isEmpty()) {
            sql.append(" AND (t.brand_std = ? OR t.brand_raw LIKE ?)");
            params.add(brand);
            params.add("%" + brand + "%");
        }
        if (priceMin != null) {
            sql.append(" AND p.price >= ?");
            params.add(priceMin);
        }
        if (priceMax != null) {
            sql.append(" AND p.price <= ?");
            params.add(priceMax);
        }

        String orderClause = switch (sort != null ? sort : "rank") {
            case "price_asc" -> " ORDER BY p.price ASC";
            case "price_desc" -> " ORDER BY p.price DESC";
            case "title" -> " ORDER BY t.title ASC";
            default -> " ORDER BY t.rank ASC";
        };
        sql.append(orderClause);
        sql.append(" LIMIT ? OFFSET ?");
        params.add(limit);
        params.add(offset);

        log.debug("Executing top items query: {}", sql);
        return clickHouseJdbcTemplate.query(sql.toString(), TOP_ITEM_ROW_MAPPER, params.toArray());
    }

    /**
     * Count total items matching filters.
     */
    public long countTopItems(String platform, String category, LocalDate eventDate,
                              String brand, Integer priceMin, Integer priceMax) {
        StringBuilder sql = new StringBuilder("""
                SELECT COUNT(*) FROM top_items t
                LEFT JOIN price_snapshots p
                    ON t.platform = p.platform AND t.item_id = p.item_id AND t.event_date = p.event_date
                WHERE 1=1
                """);
        List<Object> params = new ArrayList<>();

        if (platform != null && !platform.isEmpty()) {
            sql.append(" AND t.platform = ?");
            params.add(platform);
        }
        if (category != null && !category.isEmpty()) {
            sql.append(" AND t.category = ?");
            params.add(category);
        }
        if (eventDate != null) {
            sql.append(" AND t.event_date = ?");
            params.add(eventDate);
        }
        if (brand != null && !brand.isEmpty()) {
            sql.append(" AND (t.brand_std = ? OR t.brand_raw LIKE ?)");
            params.add(brand);
            params.add("%" + brand + "%");
        }
        if (priceMin != null) {
            sql.append(" AND p.price >= ?");
            params.add(priceMin);
        }
        if (priceMax != null) {
            sql.append(" AND p.price <= ?");
            params.add(priceMax);
        }

        Long count = clickHouseJdbcTemplate.queryForObject(sql.toString(), Long.class, params.toArray());
        return count != null ? count : 0L;
    }

    /**
     * Find a single item by platform and item_id.
     */
    public TopItemDto findItem(String platform, String itemId) {
        String sql = BASE_SELECT + """
                WHERE t.platform = ? AND t.item_id = ?
                ORDER BY t.event_date DESC
                LIMIT 1
                """;

        List<TopItemDto> results = clickHouseJdbcTemplate.query(sql, TOP_ITEM_ROW_MAPPER, platform, itemId);
        return results.isEmpty() ? null : results.get(0);
    }

    /**
     * Fetch price history for an item.
     */
    public List<TopItemDetailDto.PriceHistoryEntry> findPriceHistory(String platform, String itemId) {
        String sql = """
                SELECT event_date, price AS list_price, promo_price
                FROM price_snapshots
                WHERE platform = ? AND item_id = ?
                ORDER BY event_date ASC
                """;

        return clickHouseJdbcTemplate.query(sql, (rs, rowNum) -> TopItemDetailDto.PriceHistoryEntry.builder()
                .eventDate(rs.getObject("event_date", LocalDate.class))
                .listPrice(rs.getInt("list_price"))
                .promoPrice(rs.getObject("promo_price") != null ? rs.getInt("promo_price") : null)
                .build(), platform, itemId);
    }

    /**
     * Fetch proxy (sales/popularity) history for an item.
     */
    public List<TopItemDetailDto.ProxyHistoryEntry> findProxyHistory(String platform, String itemId) {
        String sql = """
                SELECT event_date, proxy_type, proxy_value
                FROM sales_proxy
                WHERE platform = ? AND item_id = ?
                ORDER BY event_date ASC
                """;

        return clickHouseJdbcTemplate.query(sql, (rs, rowNum) -> TopItemDetailDto.ProxyHistoryEntry.builder()
                .eventDate(rs.getObject("event_date", LocalDate.class))
                .proxyType(rs.getString("proxy_type"))
                .proxyValue(rs.getString("proxy_value"))
                .build(), platform, itemId);
    }

    /**
     * Count total items by platform for a given category and date.
     */
    public int countByPlatform(String platform, String category, LocalDate eventDate) {
        String sql = """
                SELECT COUNT(*) FROM top_items
                WHERE platform = ? AND category = ? AND event_date = ?
                """;
        Integer count = clickHouseJdbcTemplate.queryForObject(sql, Integer.class, platform, category, eventDate);
        return count != null ? count : 0;
    }
}
