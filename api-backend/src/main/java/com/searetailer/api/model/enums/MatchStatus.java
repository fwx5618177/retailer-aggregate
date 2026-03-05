package com.searetailer.api.model.enums;

import com.fasterxml.jackson.annotation.JsonValue;

public enum MatchStatus {
    AUTO_ACCEPTED("auto_accepted"),
    NEEDS_REVIEW("needs_review"),
    NO_MATCH("no_match"),
    OVERRIDDEN("overridden");

    private final String value;

    MatchStatus(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    public static MatchStatus fromValue(String value) {
        for (MatchStatus status : values()) {
            if (status.value.equalsIgnoreCase(value)) {
                return status;
            }
        }
        throw new IllegalArgumentException("Unknown MatchStatus: " + value);
    }
}
