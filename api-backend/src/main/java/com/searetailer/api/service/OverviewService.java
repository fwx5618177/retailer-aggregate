package com.searetailer.api.service;

import com.searetailer.api.model.dto.OverviewResponse;
import com.searetailer.api.repository.clickhouse.OverviewClickHouseRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;

@Service
public class OverviewService {

    private static final Logger log = LoggerFactory.getLogger(OverviewService.class);

    private final OverviewClickHouseRepository overviewRepo;

    @Value("${app.default-window-days:14}")
    private int defaultWindowDays;

    @Value("${app.default-top-n:200}")
    private int defaultTopN;

    public OverviewService(OverviewClickHouseRepository overviewRepo) {
        this.overviewRepo = overviewRepo;
    }

    /**
     * Build the full overview response for the dashboard.
     */
    public OverviewResponse getOverview(String category, LocalDate eventDate, String window) {
        if (category == null || category.isEmpty()) {
            category = "personal_care";
        }
        if (eventDate == null) {
            eventDate = LocalDate.now();
        }
        if (window == null || window.isEmpty()) {
            window = defaultWindowDays + "d";
        }

        log.info("Building overview for category={}, eventDate={}, window={}", category, eventDate, window);

        OverviewResponse.TotalItems totalItems = overviewRepo.getTotalItems(category, eventDate);
        OverviewResponse.Overlap overlap = overviewRepo.getOverlap(category, eventDate);
        int needsReviewCount = overviewRepo.getNeedsReviewCount(category, eventDate);

        // Calculate match rate
        int totalItemCount = totalItems.getTiktok() + totalItems.getShopee();
        double matchRate = totalItemCount > 0
                ? (double) overlap.getTotalMatched() * 2.0 / totalItemCount * 100.0
                : 0.0;
        matchRate = Math.round(matchRate * 100.0) / 100.0;

        List<OverviewResponse.PriceBandEntry> priceBands = overviewRepo.getPriceBandDistribution(category, eventDate);
        List<OverviewResponse.TopBrandEntry> topBrands = overviewRepo.getTopBrands(category, eventDate, 10);
        OverviewResponse.AlertsSummary alertsSummary = overviewRepo.getAlertsSummary(category, eventDate);
        OverviewResponse.Metadata metadata = overviewRepo.getMetadata(category, eventDate);

        return OverviewResponse.builder()
                .eventDate(eventDate)
                .window(window)
                .topN(defaultTopN)
                .category(category)
                .platforms(List.of("tiktok", "shopee"))
                .totalItems(totalItems)
                .overlap(overlap)
                .matchRate(matchRate)
                .needsReviewCount(needsReviewCount)
                .priceBandDistribution(priceBands)
                .topBrands(topBrands)
                .alertsSummary(alertsSummary)
                .metadata(metadata)
                .build();
    }
}
