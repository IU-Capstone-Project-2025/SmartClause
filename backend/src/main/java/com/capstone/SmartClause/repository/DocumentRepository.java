package com.capstone.SmartClause.repository;

import com.capstone.SmartClause.model.Document;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface DocumentRepository extends JpaRepository<Document, UUID> {
    
    // Find all documents in a space
    List<Document> findBySpaceIdOrderByUploadedAtDesc(UUID spaceId);
    
    // Find documents by space and user (for future authentication)
    List<Document> findBySpaceIdAndUserIdOrderByUploadedAtDesc(UUID spaceId, String userId);
    
    // Find document by ID and user (for future authentication)
    Optional<Document> findByIdAndUserId(UUID id, String userId);
    
    // Find by analysis document ID (link to analysis_results table)
    Optional<Document> findByAnalysisDocumentId(String analysisDocumentId);
    
    // Find documents by status
    List<Document> findByStatusOrderByUploadedAtDesc(Document.DocumentStatus status);
    
    // Find documents by space and status
    List<Document> findBySpaceIdAndStatusOrderByUploadedAtDesc(UUID spaceId, Document.DocumentStatus status);
    
    // Count documents in space
    long countBySpaceId(UUID spaceId);
    
    // Count documents by status in space
    long countBySpaceIdAndStatus(UUID spaceId, Document.DocumentStatus status);
    
    // Check if document exists by name in space (to prevent duplicates)
    boolean existsByNameAndSpaceId(String name, UUID spaceId);
    
    // Find document by content hash in space for duplicate detection
    Optional<Document> findByContentHashAndSpaceIdAndUserId(String contentHash, UUID spaceId, String userId);
    
    // Check if document with same content hash exists in space for user
    boolean existsByContentHashAndSpaceIdAndUserId(String contentHash, UUID spaceId, String userId);
} 