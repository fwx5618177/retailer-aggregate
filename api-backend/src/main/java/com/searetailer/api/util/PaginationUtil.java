package com.searetailer.api.util;

import com.searetailer.api.model.dto.PagedResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * Utility for pagination validation and PagedResponse construction.
 */
@Component
public class PaginationUtil {

    @Value("${app.default-page-size:20}")
    private int defaultPageSize;

    @Value("${app.max-page-size:100}")
    private int maxPageSize;

    /**
     * Validate and normalize the limit parameter.
     *
     * @param limit the requested limit, or null for default
     * @return a valid limit between 1 and maxPageSize
     */
    public int validateLimit(Integer limit) {
        if (limit == null || limit <= 0) {
            return defaultPageSize;
        }
        return Math.min(limit, maxPageSize);
    }

    /**
     * Validate and normalize the offset parameter.
     *
     * @param offset the requested offset, or null for 0
     * @return a valid offset >= 0
     */
    public int validateOffset(Integer offset) {
        if (offset == null || offset < 0) {
            return 0;
        }
        return offset;
    }

    /**
     * Build a PagedResponse from items, total count, limit, and offset.
     */
    public <T> PagedResponse<T> buildPagedResponse(List<T> items, long total, int limit, int offset) {
        boolean hasMore = (offset + limit) < total;
        return PagedResponse.<T>builder()
                .items(items)
                .total(total)
                .limit(limit)
                .offset(offset)
                .hasMore(hasMore)
                .build();
    }
}
