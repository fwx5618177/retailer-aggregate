package com.searetailer.api.model.enums;

import com.fasterxml.jackson.annotation.JsonValue;

public enum AlertStatus {
    OPEN("open"),
    ACKNOWLEDGED("acknowledged"),
    RESOLVED("resolved"),
    DISMISSED("dismissed");

    private final String value;

    AlertStatus(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    public static AlertStatus fromValue(String value) {
        for (AlertStatus status : values()) {
            if (status.value.equalsIgnoreCase(value)) {
                return status;
            }
        }
        throw new IllegalArgumentException("Unknown AlertStatus: " + value);
    }
}
