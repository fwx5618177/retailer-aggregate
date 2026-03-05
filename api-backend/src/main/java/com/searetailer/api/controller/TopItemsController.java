package com.searetailer.api.controller;

import com.searetailer.api.model.dto.PagedResponse;
import com.searetailer.api.model.dto.TopItemDto;
import com.searetailer.api.service.TopItemsService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDate;

@RestController
@RequestMapping("/api/v1")
@Tag(name = "Top Items", description = "Top-selling items listing and search")
public class TopItemsController {

    private final TopItemsService topItemsService;

    public TopItemsController(TopItemsService topItemsService) {
        this.topItemsService = topItemsService;
    }

    @GetMapping("/top-items")
    @Operation(summary = "List top-selling items",
            description = "Returns paginated list of top-selling items with optional filters.")
    public ResponseEntity<PagedResponse<TopItemDto>> getTopItems(
            @RequestParam(value = "platform", required = false)
            @Parameter(description = "Filter by platform: tiktok or shopee") String platform,

            @RequestParam(value = "category", defaultValue = "personal_care") String category,

            @RequestParam(value = "event_date", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate eventDate,

            @RequestParam(value = "window", defaultValue = "14d") String window,

            @RequestParam(value = "limit", required = false) Integer limit,

            @RequestParam(value = "offset", required = false) Integer offset,

            @RequestParam(value = "brand", required = false) String brand,

            @RequestParam(value = "price_min", required = false) Integer priceMin,

            @RequestParam(value = "price_max", required = false) Integer priceMax,

            @RequestParam(value = "sort", defaultValue = "rank")
            @Parameter(description = "Sort order: rank, price_asc, price_desc, title") String sort) {

        PagedResponse<TopItemDto> response = topItemsService.getTopItems(
                platform, category, eventDate, window, brand, priceMin, priceMax, sort, limit, offset);

        return ResponseEntity.ok(response);
    }
}
