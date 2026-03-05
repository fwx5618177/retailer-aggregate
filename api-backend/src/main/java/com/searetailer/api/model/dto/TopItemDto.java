package com.searetailer.api.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TopItemDto {

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
}
