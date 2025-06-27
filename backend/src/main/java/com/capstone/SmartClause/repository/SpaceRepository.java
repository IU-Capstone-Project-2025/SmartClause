package com.capstone.SmartClause.repository;

import com.capstone.SmartClause.model.Space;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface SpaceRepository extends JpaRepository<Space, UUID> {
    
    // Find all spaces by user (for future authentication)
    List<Space> findByUserIdOrderByCreatedAtDesc(String userId);
    
    // Find all spaces (for now, without user filtering)
    List<Space> findAllByOrderByCreatedAtDesc();
    
    // Find space by ID and user (for future authentication)
    Optional<Space> findByIdAndUserId(UUID id, String userId);
    
    // Count documents in space
    @Query("SELECT s FROM Space s LEFT JOIN FETCH s.documents WHERE s.id = :spaceId")
    Optional<Space> findByIdWithDocuments(@Param("spaceId") UUID spaceId);
    
    // Check if space exists by name for user (to prevent duplicates)
    boolean existsByNameAndUserId(String name, String userId);
    
    // Find spaces by status
    List<Space> findByStatusOrderByCreatedAtDesc(Space.SpaceStatus status);
} 