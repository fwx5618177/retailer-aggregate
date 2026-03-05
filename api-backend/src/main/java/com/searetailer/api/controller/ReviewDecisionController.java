package com.searetailer.api.controller;

import com.searetailer.api.model.dto.ReviewDecisionRequest;
import com.searetailer.api.model.dto.ReviewDecisionResponse;
import com.searetailer.api.service.ReviewService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1")
@Tag(name = "Review", description = "Review queue and decisions")
public class ReviewDecisionController {

    private final ReviewService reviewService;

    public ReviewDecisionController(ReviewService reviewService) {
        this.reviewService = reviewService;
    }

    @PostMapping("/review/{tiktokItemId}/{shopeeItemId}/decision")
    @Operation(summary = "Submit a review decision for a matching pair",
            description = "Records a human review decision (accept, reject, change_type) for a TikTok-Shopee match pair.")
    public ResponseEntity<ReviewDecisionResponse> submitDecision(
            @PathVariable("tiktokItemId") String tiktokItemId,
            @PathVariable("shopeeItemId") String shopeeItemId,
            @Valid @RequestBody ReviewDecisionRequest request,
            @RequestHeader(value = "Idempotency-Key", required = false) String idempotencyKey) {

        String reviewer = extractReviewer();

        ReviewDecisionResponse response = reviewService.submitDecision(
                tiktokItemId, shopeeItemId, request, idempotencyKey, reviewer);

        return ResponseEntity.ok(response);
    }

    /**
     * Extract the reviewer identity from the security context.
     * Falls back to "anonymous" if no authentication is present (e.g., local profile).
     */
    private String extractReviewer() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth != null && auth.getName() != null && !"anonymousUser".equals(auth.getName())) {
            return auth.getName();
        }
        return "anonymous";
    }
}
