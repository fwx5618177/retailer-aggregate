package com.searetailer.api.service;

import com.searetailer.api.model.dto.PagedResponse;
import com.searetailer.api.model.dto.TopItemDto;
import com.searetailer.api.repository.clickhouse.TopItemsClickHouseRepository;
import com.searetailer.api.util.PaginationUtil;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;

@Service
public class TopItemsService {

    private static final Logger log = LoggerFactory.getLogger(TopItemsService.class);

    private final TopItemsClickHouseRepository topItemsRepo;
    private final PaginationUtil paginationUtil;

    public TopItemsService(TopItemsClickHouseRepository topItemsRepo, PaginationUtil paginationUtil) {
        this.topItemsRepo = topItemsRepo;
        this.paginationUtil = paginationUtil;
    }

    /**
     * Get paginated top items with filters and sorting.
     */
    public PagedResponse<TopItemDto> getTopItems(String platform, String category, LocalDate eventDate,
                                                   String window, String brand, Integer priceMin,
                                                   Integer priceMax, String sort, Integer limit, Integer offset) {
        int validatedLimit = paginationUtil.validateLimit(limit);
        int validatedOffset = paginationUtil.validateOffset(offset);

        log.info("Fetching top items: platform={}, category={}, eventDate={}, sort={}, limit={}, offset={}",
                platform, category, eventDate, sort, validatedLimit, validatedOffset);

        List<TopItemDto> items = topItemsRepo.findTopItems(
                platform, category, eventDate, brand, priceMin, priceMax, sort,
                validatedLimit, validatedOffset);

        long total = topItemsRepo.countTopItems(platform, category, eventDate, brand, priceMin, priceMax);

        return paginationUtil.buildPagedResponse(items, total, validatedLimit, validatedOffset);
    }
}
