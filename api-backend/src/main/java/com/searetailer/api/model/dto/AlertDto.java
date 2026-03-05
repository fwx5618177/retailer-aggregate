package com.searetailer.api.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AlertDto {

    @JsonProperty("alert_id")
    private String alertId;

    @JsonProperty("event_date")
    private LocalDate eventDate;

    private String platform;

    @JsonProperty("item_ids")
    private List<String> itemIds;

    @JsonProperty("alert_type")
    private String alertType;

    private String severity;
    private String status;
    private String title;
    private String description;
    private Object reasons;

    @JsonProperty("suggested_action")
    private String suggestedAction;
}
