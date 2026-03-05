package com.searetailer.api.model.enums;

import com.fasterxml.jackson.annotation.JsonValue;

public enum OurStatus {
    COVERED("covered"),
    NOT_COVERED("not_covered"),
    HARVESTABLE("harvestable"),
    NOT_RECOMMENDED("not_recommended");

    private final String value;

    OurStatus(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    public static OurStatus fromValue(String value) {
        for (OurStatus status : values()) {
            if (status.value.equalsIgnoreCase(value)) {
                return status;
            }
        }
        throw new IllegalArgumentException("Unknown OurStatus: " + value);
    }
}
