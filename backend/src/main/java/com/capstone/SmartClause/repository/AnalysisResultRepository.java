package com.capstone.SmartClause.repository;

import com.capstone.SmartClause.model.AnalysisResult;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface AnalysisResultRepository extends JpaRepository<AnalysisResult, Long> {
    
    // Find analysis result by document ID (main lookup method)
    Optional<AnalysisResult> findByDocumentId(String documentId);
    
    // Find latest analysis for document (in case there are multiple)
    @Query("SELECT ar FROM AnalysisResult ar WHERE ar.documentId = :documentId ORDER BY ar.createdAt DESC")
    List<AnalysisResult> findByDocumentIdOrderByCreatedAtDesc(@Param("documentId") String documentId);
    
    // Find latest analysis result for document
    @Query("SELECT ar FROM AnalysisResult ar WHERE ar.documentId = :documentId ORDER BY ar.createdAt DESC LIMIT 1")
    Optional<AnalysisResult> findLatestByDocumentId(@Param("documentId") String documentId);
    
    // Check if analysis exists for document
    boolean existsByDocumentId(String documentId);
    
    // Delete analysis results for document
    void deleteByDocumentId(String documentId);
    
    // === CACHING METHODS ===
    
    // Find cached analysis by content hash and user (not expired)
    @Query("SELECT ar FROM AnalysisResult ar WHERE ar.contentHash = :contentHash AND ar.userId = :userId AND ar.expiresAt > :now ORDER BY ar.createdAt DESC")
    Optional<AnalysisResult> findCachedAnalysis(@Param("contentHash") String contentHash, @Param("userId") String userId, @Param("now") LocalDateTime now);
    
    // Check if cached analysis exists for content hash and user
    @Query("SELECT COUNT(ar) > 0 FROM AnalysisResult ar WHERE ar.contentHash = :contentHash AND ar.userId = :userId AND ar.expiresAt > :now")
    boolean existsCachedAnalysis(@Param("contentHash") String contentHash, @Param("userId") String userId, @Param("now") LocalDateTime now);
    
    // Find all expired cache entries for cleanup
    @Query("SELECT ar FROM AnalysisResult ar WHERE ar.expiresAt <= :now")
    List<AnalysisResult> findExpiredCacheEntries(@Param("now") LocalDateTime now);
    
    // Delete expired cache entries
    @Modifying
    @Query("DELETE FROM AnalysisResult ar WHERE ar.expiresAt <= :now")
    int deleteExpiredCacheEntries(@Param("now") LocalDateTime now);
    
    // Count cache hits and total entries for monitoring
    @Query("SELECT COUNT(ar) FROM AnalysisResult ar WHERE ar.contentHash IS NOT NULL AND ar.expiresAt > :now")
    long countActiveCacheEntries(@Param("now") LocalDateTime now);
    
    @Query("SELECT COUNT(ar) FROM AnalysisResult ar WHERE ar.userId = :userId AND ar.contentHash IS NOT NULL AND ar.expiresAt > :now")
    long countActiveCacheEntriesForUser(@Param("userId") String userId, @Param("now") LocalDateTime now);
} 