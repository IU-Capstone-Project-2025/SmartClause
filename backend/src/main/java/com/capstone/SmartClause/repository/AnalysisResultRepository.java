package com.capstone.SmartClause.repository;

import com.capstone.SmartClause.model.AnalysisResult;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

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
} 