package com.searetailer.api.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ReviewQueueItemDto {

    @JsonProperty("tiktok_item_id")
    private String tiktokItemId;

    @JsonProperty("shopee_item_id")
    private String shopeeItemId;

    @JsonProperty("tiktok_item")
    private TopItemDto tiktokItem;

    @JsonProperty("shopee_item")
    private TopItemDto shopeeItem;

    @JsonProperty("match_type")
    private String matchType;

    private Double confidence;

    private Object reasons;

    @JsonProperty("rule_version")
    private String ruleVersion;
}
