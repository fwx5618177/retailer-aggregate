package com.searetailer.api.controller;

import com.searetailer.api.model.dto.TopItemDetailDto;
import com.searetailer.api.service.ItemDetailService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1")
@Tag(name = "Top Items", description = "Item detail with history and matches")
public class ItemDetailController {

    private final ItemDetailService itemDetailService;

    public ItemDetailController(ItemDetailService itemDetailService) {
        this.itemDetailService = itemDetailService;
    }

    @GetMapping("/items/{platform}/{itemId}")
    @Operation(summary = "Get item detail with history and matches",
            description = "Returns full item detail including price history, proxy history, and cross-platform matches.")
    public ResponseEntity<TopItemDetailDto> getItemDetail(
            @PathVariable("platform") String platform,
            @PathVariable("itemId") String itemId) {

        TopItemDetailDto detail = itemDetailService.getItemDetail(platform, itemId);
        return ResponseEntity.ok(detail);
    }
}
