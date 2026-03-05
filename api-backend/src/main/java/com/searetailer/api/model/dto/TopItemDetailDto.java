package com.searetailer.api.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TopItemDetailDto {

    // Base item fields
    @JsonProperty("event_date")
    private LocalDate eventDate;

    private String platform;

    @JsonProperty("item_id")
    private String itemId;

    private String title;
    private String category;
    private Integer rank;
    private String url;

    @JsonProperty("brand_raw")
    private String brandRaw;

    @JsonProperty("brand_std")
    private String brandStd;

    @JsonProperty("size_value")
    private Double sizeValue;

    @JsonProperty("size_unit")
    private String sizeUnit;

    @JsonProperty("pack_count")
    private Integer packCount;

    @JsonProperty("image_url")
    private String imageUrl;

    @JsonProperty("list_price")
    private Integer listPrice;

    @JsonProperty("promo_price")
    private Integer promoPrice;

    private String currency;

    @JsonProperty("review_count")
    private Integer reviewCount;

    @JsonProperty("sold_range")
    private String soldRange;

    @JsonProperty("source_type")
    private String sourceType;

    // Extended fields
    @JsonProperty("price_history")
    private List<PriceHistoryEntry> priceHistory;

    @JsonProperty("proxy_history")
    private List<ProxyHistoryEntry> proxyHistory;

    private List<MatchResultDto> matches;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class PriceHistoryEntry {
        @JsonProperty("event_date")
        private LocalDate eventDate;

        @JsonProperty("list_price")
        private Integer listPrice;

        @JsonProperty("promo_price")
        private Integer promoPrice;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class ProxyHistoryEntry {
        @JsonProperty("event_date")
        private LocalDate eventDate;

        @JsonProperty("proxy_type")
        private String proxyType;

        @JsonProperty("proxy_value")
        private String proxyValue;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class MatchResultDto {
        @JsonProperty("tiktok_item_id")
        private String tiktokItemId;

        @JsonProperty("shopee_item_id")
        private String shopeeItemId;

        @JsonProperty("tiktok_title")
        private String tiktokTitle;

        @JsonProperty("shopee_title")
        private String shopeeTitle;

        @JsonProperty("match_type")
        private String matchType;

        private Double confidence;

        private String status;

        private Object reasons;

        @JsonProperty("rule_version")
        private String ruleVersion;
    }
}
