package com.capstone.SmartClause.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "documents")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Document {
    
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;
    
    @Column(nullable = false, length = 255)
    private String name;
    
    @Column(name = "original_filename", length = 255)
    private String originalFilename;
    
    @Column(name = "file_path", length = 500)
    private String filePath;
    
    @Column(nullable = false)
    private Long size;
    
    @Column(name = "content_type", length = 100)
    private String contentType;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private DocumentStatus status = DocumentStatus.UPLOADING;
    
    @CreationTimestamp
    @Column(name = "uploaded_at", nullable = false, updatable = false)
    private LocalDateTime uploadedAt;
    
    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "space_id", nullable = false)
    private Space space;
    
    // For future authentication implementation
    @Column(name = "user_id", length = 255)
    private String userId;
    
    // Link to existing analysis_results table via document_id string
    @Column(name = "analysis_document_id", length = 255)
    private String analysisDocumentId;
    
    @Lob
    @Column(name = "content")
    private byte[] content;
    
    public enum DocumentStatus {
        UPLOADING, PROCESSING, COMPLETED, ERROR
    }
} 