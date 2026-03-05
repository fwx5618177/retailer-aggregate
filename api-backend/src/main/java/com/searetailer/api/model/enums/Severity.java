package com.searetailer.api.model.enums;

import com.fasterxml.jackson.annotation.JsonValue;

public enum Severity {
    CRITICAL("critical"),
    HIGH("high"),
    MEDIUM("medium"),
    LOW("low");

    private final String value;

    Severity(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    public static Severity fromValue(String value) {
        for (Severity s : values()) {
            if (s.value.equalsIgnoreCase(value)) {
                return s;
            }
        }
        throw new IllegalArgumentException("Unknown Severity: " + value);
    }
}
