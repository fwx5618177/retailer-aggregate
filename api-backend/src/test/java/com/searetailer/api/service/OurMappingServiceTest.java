package com.searetailer.api.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.searetailer.api.exception.ResourceNotFoundException;
import com.searetailer.api.model.dto.OurMappingRequest;
import com.searetailer.api.model.dto.OurMappingResponse;
import com.searetailer.api.model.entity.OurMappingEntity;
import com.searetailer.api.repository.postgres.OurMappingRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.OffsetDateTime;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class OurMappingServiceTest {

    @Mock
    private OurMappingRepository ourMappingRepo;

    @Mock
    private AuditService auditService;

    private OurMappingService ourMappingService;

    @BeforeEach
    void setUp() {
        ObjectMapper objectMapper = new ObjectMapper();
        ourMappingService = new OurMappingService(ourMappingRepo, auditService, objectMapper);
    }

    @Test
    void getMapping_existingMapping_returnsResponse() {
        // Given
        OurMappingEntity entity = OurMappingEntity.builder()
                .id(UUID.randomUUID())
                .platform("tiktok")
                .itemId("tt_123")
                .ourStatus("covered")
                .ourSkuId("SKU-001")
                .notes("Test notes")
                .updatedBy("admin")
                .updatedAt(OffsetDateTime.now())
                .build();

        when(ourMappingRepo.findByPlatformAndItemId("tiktok", "tt_123"))
                .thenReturn(Optional.of(entity));

        // When
        OurMappingResponse response = ourMappingService.getMapping("tiktok", "tt_123");

        // Then
        assertThat(response).isNotNull();
        assertThat(response.getPlatform()).isEqualTo("tiktok");
        assertThat(response.getOurStatus()).isEqualTo("covered");
        assertThat(response.getOurSkuId()).isEqualTo("SKU-001");
    }

    @Test
    void getMapping_nonExisting_throwsNotFound() {
        when(ourMappingRepo.findByPlatformAndItemId("tiktok", "tt_999"))
                .thenReturn(Optional.empty());

        assertThatThrownBy(() -> ourMappingService.getMapping("tiktok", "tt_999"))
                .isInstanceOf(ResourceNotFoundException.class);
    }

    @Test
    void upsertMapping_createNew_returnsCreated() {
        // Given
        when(ourMappingRepo.findByPlatformAndItemId("shopee", "sh_001"))
                .thenReturn(Optional.empty());
        when(ourMappingRepo.save(any(OurMappingEntity.class)))
                .thenAnswer(invocation -> invocation.getArgument(0));

        OurMappingRequest request = new OurMappingRequest();
        request.setOurStatus("harvestable");
        request.setOurSkuId("SKU-NEW");
        request.setNotes("New mapping");

        // When
        Map<String, String> result = ourMappingService.upsertMapping(
                "shopee", "sh_001", request, "admin@test.com");

        // Then
        assertThat(result.get("status")).isEqualTo("ok");
        assertThat(result.get("message")).contains("created");
        verify(ourMappingRepo).save(any(OurMappingEntity.class));
    }

    @Test
    void upsertMapping_updateExisting_returnsUpdated() {
        // Given
        OurMappingEntity existing = OurMappingEntity.builder()
                .id(UUID.randomUUID())
                .platform("shopee")
                .itemId("sh_001")
                .ourStatus("not_covered")
                .updatedAt(OffsetDateTime.now())
                .build();

        when(ourMappingRepo.findByPlatformAndItemId("shopee", "sh_001"))
                .thenReturn(Optional.of(existing));
        when(ourMappingRepo.save(any(OurMappingEntity.class)))
                .thenAnswer(invocation -> invocation.getArgument(0));

        OurMappingRequest request = new OurMappingRequest();
        request.setOurStatus("covered");
        request.setOurSkuId("SKU-UPD");

        // When
        Map<String, String> result = ourMappingService.upsertMapping(
                "shopee", "sh_001", request, "admin@test.com");

        // Then
        assertThat(result.get("status")).isEqualTo("ok");
        assertThat(result.get("message")).contains("updated");
    }
}
