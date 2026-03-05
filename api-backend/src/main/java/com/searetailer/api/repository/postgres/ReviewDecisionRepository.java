package com.searetailer.api.repository.postgres;

import com.searetailer.api.model.entity.ReviewDecision;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ReviewDecisionRepository extends JpaRepository<ReviewDecision, UUID> {

    Optional<ReviewDecision> findByIdempotencyKey(String idempotencyKey);

    List<ReviewDecision> findByTiktokItemIdAndShopeeItemIdOrderByCreatedAtDesc(
            String tiktokItemId, String shopeeItemId);

    boolean existsByIdempotencyKey(String idempotencyKey);
}
