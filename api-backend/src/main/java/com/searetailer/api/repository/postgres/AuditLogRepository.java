package com.searetailer.api.repository.postgres;

import com.searetailer.api.model.entity.AuditLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface AuditLogRepository extends JpaRepository<AuditLog, UUID> {

    List<AuditLog> findByEntityTypeAndEntityIdOrderByCreatedAtDesc(String entityType, String entityId);

    List<AuditLog> findByActorOrderByCreatedAtDesc(String actor);

    List<AuditLog> findByBatchIdOrderByCreatedAtDesc(String batchId);
}
