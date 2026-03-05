package com.searetailer.api.service;

import com.searetailer.api.model.entity.AuditLog;
import com.searetailer.api.repository.postgres.AuditLogRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.OffsetDateTime;

@Service
public class AuditService {

    private static final Logger log = LoggerFactory.getLogger(AuditService.class);

    private final AuditLogRepository auditLogRepository;

    public AuditService(AuditLogRepository auditLogRepository) {
        this.auditLogRepository = auditLogRepository;
    }

    /**
     * Record an audit log entry for any tracked action.
     *
     * @param entityType  the type of entity (e.g., "review_decision", "our_mapping")
     * @param entityId    the unique identifier of the entity
     * @param action      the action performed (e.g., "create", "update", "approve", "reject")
     * @param oldValue    JSON string of the old value (nullable)
     * @param newValue    JSON string of the new value (nullable)
     * @param comment     optional comment
     * @param actor       the user who performed the action
     * @param batchId     optional batch identifier
     * @param ruleVersion optional rule version
     */
    public void recordAudit(String entityType, String entityId, String action,
                             String oldValue, String newValue, String comment,
                             String actor, String batchId, String ruleVersion) {
        AuditLog auditLog = AuditLog.builder()
                .entityType(entityType)
                .entityId(entityId)
                .action(action)
                .oldValue(oldValue)
                .newValue(newValue)
                .comment(comment)
                .actor(actor)
                .batchId(batchId)
                .ruleVersion(ruleVersion)
                .createdAt(OffsetDateTime.now())
                .build();

        auditLogRepository.save(auditLog);
        log.info("Audit log created: entityType={}, entityId={}, action={}, actor={}",
                entityType, entityId, action, actor);
    }
}
