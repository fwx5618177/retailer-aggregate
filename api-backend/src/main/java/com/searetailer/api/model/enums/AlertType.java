package com.searetailer.api.model.enums;

import com.fasterxml.jackson.annotation.JsonValue;

public enum AlertType {
    RANK_JUMP("rank_jump"),
    PROXY_SPIKE("proxy_spike"),
    PLATFORM_GAP("platform_gap"),
    PRICE_ANOMALY("price_anomaly");

    private final String value;

    AlertType(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    public static AlertType fromValue(String value) {
        for (AlertType type : values()) {
            if (type.value.equalsIgnoreCase(value)) {
                return type;
            }
        }
        throw new IllegalArgumentException("Unknown AlertType: " + value);
    }
}
