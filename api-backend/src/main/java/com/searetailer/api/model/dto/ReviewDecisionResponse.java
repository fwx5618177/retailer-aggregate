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
public class ReviewDecisionResponse {

    @JsonProperty("decision_id")
    private String decisionId;

    private String status;
    private String message;
}
