package com.searetailer.api.model.enums;

import com.fasterxml.jackson.annotation.JsonValue;

public enum MatchType {
    EXACT_SAME("exact_same"),
    VARIANT_FAMILY("variant_family"),
    SIMILAR("similar"),
    NO_MATCH("no_match");

    private final String value;

    MatchType(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    public static MatchType fromValue(String value) {
        for (MatchType type : values()) {
            if (type.value.equalsIgnoreCase(value)) {
                return type;
            }
        }
        throw new IllegalArgumentException("Unknown MatchType: " + value);
    }
}
