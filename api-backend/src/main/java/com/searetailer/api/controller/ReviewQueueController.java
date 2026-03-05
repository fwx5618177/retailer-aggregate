package com.searetailer.api.controller;

import com.searetailer.api.model.dto.PagedResponse;
import com.searetailer.api.model.dto.ReviewQueueItemDto;
import com.searetailer.api.service.ReviewService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1")
@Tag(name = "Review", description = "Review queue and decisions")
public class ReviewQueueController {

    private final ReviewService reviewService;

    public ReviewQueueController(ReviewService reviewService) {
        this.reviewService = reviewService;
    }

    @GetMapping("/review-queue")
    @Operation(summary = "List items pending human review",
            description = "Returns paginated list of match pairs that require human review.")
    public ResponseEntity<PagedResponse<ReviewQueueItemDto>> getReviewQueue(
            @RequestParam(value = "category", defaultValue = "personal_care") String category,

            @RequestParam(value = "limit", required = false) Integer limit,

            @RequestParam(value = "offset", required = false) Integer offset,

            @RequestParam(value = "sort", defaultValue = "confidence_desc")
            @Parameter(description = "Sort order: confidence_asc, confidence_desc, date_desc")
            String sort) {

        PagedResponse<ReviewQueueItemDto> response = reviewService.getReviewQueue(
                category, sort, limit, offset);

        return ResponseEntity.ok(response);
    }
}
