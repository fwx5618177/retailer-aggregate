package com.searetailer.api.controller;

import com.searetailer.api.model.dto.OurMappingRequest;
import com.searetailer.api.model.dto.OurMappingResponse;
import com.searetailer.api.service.OurMappingService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/v1")
@Tag(name = "Our Mapping", description = "Internal product mapping management")
public class OurMappingController {

    private final OurMappingService ourMappingService;

    public OurMappingController(OurMappingService ourMappingService) {
        this.ourMappingService = ourMappingService;
    }

    @GetMapping("/our-mapping/{platform}/{itemId}")
    @Operation(summary = "Get our mapping for an item",
            description = "Returns internal mapping status and SKU for a given platform item.")
    public ResponseEntity<OurMappingResponse> getMapping(
            @PathVariable("platform") String platform,
            @PathVariable("itemId") String itemId) {

        OurMappingResponse response = ourMappingService.getMapping(platform, itemId);
        return ResponseEntity.ok(response);
    }

    @PostMapping("/our-mapping/{platform}/{itemId}")
    @Operation(summary = "Update our mapping for an item",
            description = "Create or update internal mapping (status, SKU, notes) for a given platform item.")
    public ResponseEntity<Map<String, String>> updateMapping(
            @PathVariable("platform") String platform,
            @PathVariable("itemId") String itemId,
            @Valid @RequestBody OurMappingRequest request) {

        String actor = extractActor();
        Map<String, String> result = ourMappingService.upsertMapping(platform, itemId, request, actor);
        return ResponseEntity.ok(result);
    }

    private String extractActor() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth != null && auth.getName() != null && !"anonymousUser".equals(auth.getName())) {
            return auth.getName();
        }
        return "anonymous";
    }
}
