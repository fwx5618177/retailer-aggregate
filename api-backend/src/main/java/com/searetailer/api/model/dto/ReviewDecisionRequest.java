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
public class ReviewDecisionRequest {

    @NotBlank(message = "Decision is required")
    @Pattern(regexp = "accept|reject|change_type", message = "Decision must be one of: accept, reject, change_type")
    private String decision;

    @JsonProperty("new_match_type")
    private String newMatchType;

    private String comment;
}
