package com.searetailer.api.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.OffsetDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class OurMappingResponse {

    private String platform;

    @JsonProperty("item_id")
    private String itemId;

    @JsonProperty("our_status")
    private String ourStatus;

    @JsonProperty("our_sku_id")
    private String ourSkuId;

    private String notes;

    @JsonProperty("updated_by")
    private String updatedBy;

    @JsonProperty("updated_at")
    private OffsetDateTime updatedAt;
}
