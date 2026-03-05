package com.searetailer.api.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.searetailer.api.exception.IdempotencyConflictException;
import com.searetailer.api.model.dto.PagedResponse;
import com.searetailer.api.model.dto.ReviewDecisionRequest;
import com.searetailer.api.model.dto.ReviewDecisionResponse;
import com.searetailer.api.model.dto.ReviewQueueItemDto;
import com.searetailer.api.model.entity.ReviewDecision;
import com.searetailer.api.repository.clickhouse.MatchMapClickHouseRepository;
import com.searetailer.api.repository.postgres.ReviewDecisionRepository;
import com.searetailer.api.util.PaginationUtil;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
public class ReviewService {

    private static final Logger log = LoggerFactory.getLogger(ReviewService.class);

    private final MatchMapClickHouseRepository matchMapRepo;
    private final ReviewDecisionRepository reviewDecisionRepo;
    private final AuditService auditService;
    private final PaginationUtil paginationUtil;
    private final ObjectMapper objectMapper;

    public ReviewService(MatchMapClickHouseRepository matchMapRepo,
                          ReviewDecisionRepository reviewDecisionRepo,
                          AuditService auditService,
                          PaginationUtil paginationUtil,
                          ObjectMapper objectMapper) {
        this.matchMapRepo = matchMapRepo;
        this.reviewDecisionRepo = reviewDecisionRepo;
        this.auditService = auditService;
        this.paginationUtil = paginationUtil;
        this.objectMapper = objectMapper;
    }

    /**
     * Get the review queue: matches that need human review.
     */
    public PagedResponse<ReviewQueueItemDto> getReviewQueue(String category, String sort,
                                                              Integer limit, Integer offset) {
        int validatedLimit = paginationUtil.validateLimit(limit);
        int validatedOffset = paginationUtil.validateOffset(offset);

        log.info("Fetching review queue: category={}, sort={}, limit={}, offset={}",
                category, sort, validatedLimit, validatedOffset);

        List<ReviewQueueItemDto> items = matchMapRepo.findReviewQueue(
                category, sort, validatedLimit, validatedOffset);

        long total = matchMapRepo.countReviewQueue(category);

        return paginationUtil.buildPagedResponse(items, total, validatedLimit, validatedOffset);
    }

    /**
     * Submit a review decision for a matching pair.
     * Writes to Postgres (review_decisions) and creates an audit log entry.
     * Supports idempotency via the Idempotency-Key header.
     */
    @Transactional
    public ReviewDecisionResponse submitDecision(String tiktokItemId, String shopeeItemId,
                                                   ReviewDecisionRequest request,
                                                   String idempotencyKey, String reviewer) {
        log.info("Submitting review decision: tiktok={}, shopee={}, decision={}, reviewer={}",
                tiktokItemId, shopeeItemId, request.getDecision(), reviewer);

        // Check idempotency key
        if (idempotencyKey != null && !idempotencyKey.isEmpty()) {
            Optional<ReviewDecision> existing = reviewDecisionRepo.findByIdempotencyKey(idempotencyKey);
            if (existing.isPresent()) {
                ReviewDecision prev = existing.get();
                log.warn("Duplicate submission detected for idempotency key: {}", idempotencyKey);
                throw new IdempotencyConflictException(
                        "Duplicate submission. Previous decision ID: " + prev.getId());
            }
        }

        // Look up the current match status from ClickHouse
        String currentStatus = matchMapRepo.getMatchStatus(tiktokItemId, shopeeItemId);

        // Determine the new status based on decision
        String newStatus = determineNewStatus(request.getDecision());

        // Build and save the review decision entity
        ReviewDecision decision = ReviewDecision.builder()
                .tiktokItemId(tiktokItemId)
                .shopeeItemId(shopeeItemId)
                .decision(request.getDecision())
                .matchType(request.getNewMatchType())
                .comment(request.getComment())
                .reviewer(reviewer)
                .idempotencyKey(idempotencyKey)
                .oldStatus(currentStatus)
                .newStatus(newStatus)
                .createdAt(OffsetDateTime.now())
                .build();

        ReviewDecision saved = reviewDecisionRepo.save(decision);

        // Create audit log entry
        String entityId = tiktokItemId + ":" + shopeeItemId;
        String oldValueJson = toJson(Map.of("status", currentStatus != null ? currentStatus : "unknown"));
        String newValueJson = toJson(Map.of(
                "status", newStatus,
                "decision", request.getDecision(),
                "match_type", request.getNewMatchType() != null ? request.getNewMatchType() : "",
                "comment", request.getComment() != null ? request.getComment() : ""
        ));

        auditService.recordAudit(
                "review_decision",
                entityId,
                "review_" + request.getDecision(),
                oldValueJson,
                newValueJson,
                request.getComment(),
                reviewer,
                null,
                null
        );

        return ReviewDecisionResponse.builder()
                .decisionId(saved.getId().toString())
                .status("recorded")
                .message("Review decision recorded successfully")
                .build();
    }

    private String determineNewStatus(String decision) {
        return switch (decision) {
            case "accept" -> "auto_accepted";
            case "reject" -> "no_match";
            case "change_type" -> "overridden";
            default -> "needs_review";
        };
    }

    private String toJson(Object obj) {
        try {
            return objectMapper.writeValueAsString(obj);
        } catch (JsonProcessingException e) {
            log.warn("Failed to serialize object to JSON", e);
            return "{}";
        }
    }
}
