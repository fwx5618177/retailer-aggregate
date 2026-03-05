package com.searetailer.api.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class OverviewResponse {

    @JsonProperty("event_date")
    private LocalDate eventDate;

    private String window;

    @JsonProperty("top_n")
    private Integer topN;

    private String category;

    private List<String> platforms;

    @JsonProperty("total_items")
    private TotalItems totalItems;

    private Overlap overlap;

    @JsonProperty("match_rate")
    private Double matchRate;

    @JsonProperty("needs_review_count")
    private Integer needsReviewCount;

    @JsonProperty("price_band_distribution")
    private List<PriceBandEntry> priceBandDistribution;

    @JsonProperty("top_brands")
    private List<TopBrandEntry> topBrands;

    @JsonProperty("alerts_summary")
    private AlertsSummary alertsSummary;

    private Metadata metadata;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class TotalItems {
        private Integer tiktok;
        private Integer shopee;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class Overlap {
        @JsonProperty("exact_same")
        private Integer exactSame;

        @JsonProperty("variant_family")
        private Integer variantFamily;

        private Integer similar;

        @JsonProperty("total_matched")
        private Integer totalMatched;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class PriceBandEntry {
        private String band;

        @JsonProperty("tiktok_count")
        private Integer tiktokCount;

        @JsonProperty("shopee_count")
        private Integer shopeeCount;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class TopBrandEntry {
        private String brand;

        @JsonProperty("tiktok_count")
        private Integer tiktokCount;

        @JsonProperty("shopee_count")
        private Integer shopeeCount;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class AlertsSummary {
        private Integer total;

        @JsonProperty("by_severity")
        private Map<String, Integer> bySeverity;

        @JsonProperty("by_type")
        private Map<String, Integer> byType;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class Metadata {
        @JsonProperty("schema_version")
        private String schemaVersion;

        @JsonProperty("rule_version")
        private String ruleVersion;

        @JsonProperty("batch_id")
        private String batchId;

        @JsonProperty("dq_status")
        private String dqStatus;
    }
}
