package com.searetailer.api.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class OurMappingRequest {

    @NotBlank(message = "our_status is required")
    @Pattern(regexp = "covered|not_covered|harvestable|not_recommended",
            message = "our_status must be one of: covered, not_covered, harvestable, not_recommended")
    @JsonProperty("our_status")
    private String ourStatus;

    @JsonProperty("our_sku_id")
    private String ourSkuId;

    private String notes;
}
