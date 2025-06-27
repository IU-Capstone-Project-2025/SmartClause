package com.capstone.SmartClause.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "spaces")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Space {
    
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "UUID")
    private UUID id;
    
    @Column(nullable = false, length = 255)
    private String name;
    
    @Column(columnDefinition = "TEXT")
    private String description;
    
    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
    
    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    
    // For future authentication implementation
    @Column(name = "user_id", length = 255)
    private String userId;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private SpaceStatus status = SpaceStatus.ACTIVE;
    
    @OneToMany(mappedBy = "space", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<Document> documents;
    
    public enum SpaceStatus {
        ACTIVE, PROCESSING, ERROR
    }
    
    // Helper method to get documents count
    public int getDocumentsCount() {
        return documents != null ? documents.size() : 0;
    }
} 