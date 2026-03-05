package com.searetailer.api.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.searetailer.api.exception.ResourceNotFoundException;
import com.searetailer.api.model.dto.OurMappingRequest;
import com.searetailer.api.model.dto.OurMappingResponse;
import com.searetailer.api.model.entity.OurMappingEntity;
import com.searetailer.api.repository.postgres.OurMappingRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.Map;
import java.util.Optional;

@Service
public class OurMappingService {

    private static final Logger log = LoggerFactory.getLogger(OurMappingService.class);

    private final OurMappingRepository ourMappingRepo;
    private final AuditService auditService;
    private final ObjectMapper objectMapper;

    public OurMappingService(OurMappingRepository ourMappingRepo,
                              AuditService auditService,
                              ObjectMapper objectMapper) {
        this.ourMappingRepo = ourMappingRepo;
        this.auditService = auditService;
        this.objectMapper = objectMapper;
    }

    /**
     * Get our mapping for a specific platform and item.
     */
    public OurMappingResponse getMapping(String platform, String itemId) {
        log.info("Fetching our mapping: platform={}, itemId={}", platform, itemId);

        OurMappingEntity entity = ourMappingRepo.findByPlatformAndItemId(platform, itemId)
                .orElseThrow(() -> new ResourceNotFoundException(
                        "Mapping not found for " + platform + "/" + itemId));

        return toResponse(entity);
    }

    /**
     * Create or update our mapping for a specific platform and item.
     */
    @Transactional
    public Map<String, String> upsertMapping(String platform, String itemId,
                                               OurMappingRequest request, String actor) {
        log.info("Upserting our mapping: platform={}, itemId={}, status={}, actor={}",
                platform, itemId, request.getOurStatus(), actor);

        Optional<OurMappingEntity> existing = ourMappingRepo.findByPlatformAndItemId(platform, itemId);

        String action;
        String oldValueJson = null;

        if (existing.isPresent()) {
            OurMappingEntity entity = existing.get();
            oldValueJson = toJson(Map.of(
                    "our_status", entity.getOurStatus(),
                    "our_sku_id", entity.getOurSkuId() != null ? entity.getOurSkuId() : "",
                    "notes", entity.getNotes() != null ? entity.getNotes() : ""
            ));

            entity.setOurStatus(request.getOurStatus());
            entity.setOurSkuId(request.getOurSkuId());
            entity.setNotes(request.getNotes());
            entity.setUpdatedBy(actor);
            entity.setUpdatedAt(OffsetDateTime.now());
            ourMappingRepo.save(entity);
            action = "update";
        } else {
            OurMappingEntity entity = OurMappingEntity.builder()
                    .platform(platform)
                    .itemId(itemId)
                    .ourStatus(request.getOurStatus())
                    .ourSkuId(request.getOurSkuId())
                    .notes(request.getNotes())
                    .updatedBy(actor)
                    .updatedAt(OffsetDateTime.now())
                    .build();
            ourMappingRepo.save(entity);
            action = "create";
        }

        String newValueJson = toJson(Map.of(
                "our_status", request.getOurStatus(),
                "our_sku_id", request.getOurSkuId() != null ? request.getOurSkuId() : "",
                "notes", request.getNotes() != null ? request.getNotes() : ""
        ));

        // Create audit log
        auditService.recordAudit(
                "our_mapping",
                platform + ":" + itemId,
                action,
                oldValueJson,
                newValueJson,
                null,
                actor,
                null,
                null
        );

        return Map.of(
                "status", "ok",
                "message", "Mapping " + (action.equals("create") ? "created" : "updated") + " successfully"
        );
    }

    private OurMappingResponse toResponse(OurMappingEntity entity) {
        return OurMappingResponse.builder()
                .platform(entity.getPlatform())
                .itemId(entity.getItemId())
                .ourStatus(entity.getOurStatus())
                .ourSkuId(entity.getOurSkuId())
                .notes(entity.getNotes())
                .updatedBy(entity.getUpdatedBy())
                .updatedAt(entity.getUpdatedAt())
                .build();
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
