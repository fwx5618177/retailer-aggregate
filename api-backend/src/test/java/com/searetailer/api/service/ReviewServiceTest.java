package com.searetailer.api.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.searetailer.api.exception.IdempotencyConflictException;
import com.searetailer.api.model.dto.ReviewDecisionRequest;
import com.searetailer.api.model.dto.ReviewDecisionResponse;
import com.searetailer.api.model.entity.ReviewDecision;
import com.searetailer.api.repository.clickhouse.MatchMapClickHouseRepository;
import com.searetailer.api.repository.postgres.ReviewDecisionRepository;
import com.searetailer.api.util.PaginationUtil;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ReviewServiceTest {

    @Mock
    private MatchMapClickHouseRepository matchMapRepo;

    @Mock
    private ReviewDecisionRepository reviewDecisionRepo;

    @Mock
    private AuditService auditService;

    @Mock
    private PaginationUtil paginationUtil;

    private ReviewService reviewService;

    @BeforeEach
    void setUp() {
        ObjectMapper objectMapper = new ObjectMapper();
        reviewService = new ReviewService(matchMapRepo, reviewDecisionRepo, auditService,
                paginationUtil, objectMapper);
    }

    @Test
    void submitDecision_success() {
        // Given
        String tiktokId = "tt_123";
        String shopeeId = "sh_456";
        ReviewDecisionRequest request = new ReviewDecisionRequest();
        request.setDecision("accept");
        request.setComment("Looks correct");

        when(matchMapRepo.getMatchStatus(tiktokId, shopeeId)).thenReturn("needs_review");

        ReviewDecision saved = ReviewDecision.builder()
                .id(UUID.randomUUID())
                .tiktokItemId(tiktokId)
                .shopeeItemId(shopeeId)
                .decision("accept")
                .build();
        when(reviewDecisionRepo.save(any(ReviewDecision.class))).thenReturn(saved);

        // When
        ReviewDecisionResponse response = reviewService.submitDecision(
                tiktokId, shopeeId, request, null, "reviewer@test.com");

        // Then
        assertThat(response).isNotNull();
        assertThat(response.getStatus()).isEqualTo("recorded");
        assertThat(response.getDecisionId()).isNotNull();
        verify(reviewDecisionRepo).save(any(ReviewDecision.class));
        verify(auditService).recordAudit(anyString(), anyString(), anyString(),
                anyString(), anyString(), anyString(), anyString(), any(), any());
    }

    @Test
    void submitDecision_duplicateIdempotencyKey_throwsConflict() {
        // Given
        String idempotencyKey = "unique-key-123";
        ReviewDecision existingDecision = ReviewDecision.builder()
                .id(UUID.randomUUID())
                .idempotencyKey(idempotencyKey)
                .build();

        when(reviewDecisionRepo.findByIdempotencyKey(idempotencyKey))
                .thenReturn(Optional.of(existingDecision));

        ReviewDecisionRequest request = new ReviewDecisionRequest();
        request.setDecision("accept");

        // When / Then
        assertThatThrownBy(() -> reviewService.submitDecision(
                "tt_123", "sh_456", request, idempotencyKey, "reviewer@test.com"))
                .isInstanceOf(IdempotencyConflictException.class)
                .hasMessageContaining("Duplicate submission");
    }
}
