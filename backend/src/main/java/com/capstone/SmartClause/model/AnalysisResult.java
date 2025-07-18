package com.capstone.SmartClause.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;
import java.util.Map;

@Entity
@Table(name = "analysis_results")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class AnalysisResult {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "document_id", nullable = false, length = 255)
    private String documentId;
    
    // User ID for user-specific caching
    @Column(name = "user_id", length = 255)
    private String userId;
    
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "analysis_points", columnDefinition = "jsonb")
    private Map<String, Object> analysisPoints;
    
    // Content hash for caching lookups
    @Column(name = "content_hash", length = 64)
    private String contentHash;
    
    // Cache expiry time (default 1 hour from creation)
    @Column(name = "expires_at")
    private LocalDateTime expiresAt;
    
    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
} 