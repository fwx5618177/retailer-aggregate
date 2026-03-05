package com.searetailer.api.model.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "our_mapping", uniqueConstraints = {
        @UniqueConstraint(name = "uk_mapping", columnNames = {"platform", "item_id"})
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class OurMappingEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "platform", nullable = false, length = 16)
    private String platform;

    @Column(name = "item_id", nullable = false, length = 64)
    private String itemId;

    @Column(name = "our_status", nullable = false, length = 32)
    private String ourStatus;

    @Column(name = "our_sku_id", length = 64)
    private String ourSkuId;

    @Column(name = "notes", columnDefinition = "TEXT")
    private String notes;

    @Column(name = "updated_by", length = 128)
    private String updatedBy;

    @Column(name = "updated_at")
    @Builder.Default
    private OffsetDateTime updatedAt = OffsetDateTime.now();
}
