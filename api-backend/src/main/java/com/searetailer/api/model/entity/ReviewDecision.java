package com.searetailer.api.model.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "review_decisions")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ReviewDecision {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "tiktok_item_id", nullable = false, length = 64)
    private String tiktokItemId;

    @Column(name = "shopee_item_id", nullable = false, length = 64)
    private String shopeeItemId;

    @Column(name = "decision", nullable = false, length = 32)
    private String decision;

    @Column(name = "match_type", length = 32)
    private String matchType;

    @Column(name = "comment", columnDefinition = "TEXT")
    private String comment;

    @Column(name = "reviewer", nullable = false, length = 128)
    private String reviewer;

    @Column(name = "rule_version", length = 16)
    private String ruleVersion;

    @Column(name = "batch_id", length = 64)
    private String batchId;

    @Column(name = "idempotency_key", length = 128, unique = true)
    private String idempotencyKey;

    @Column(name = "old_status", length = 32)
    private String oldStatus;

    @Column(name = "new_status", length = 32)
    private String newStatus;

    @Column(name = "created_at")
    @Builder.Default
    private OffsetDateTime createdAt = OffsetDateTime.now();
}
