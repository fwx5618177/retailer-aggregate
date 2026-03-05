package com.searetailer.api.repository.postgres;

import com.searetailer.api.model.entity.OurMappingEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface OurMappingRepository extends JpaRepository<OurMappingEntity, UUID> {

    Optional<OurMappingEntity> findByPlatformAndItemId(String platform, String itemId);

    boolean existsByPlatformAndItemId(String platform, String itemId);
}
