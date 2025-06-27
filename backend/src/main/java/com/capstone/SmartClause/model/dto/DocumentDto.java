package com.capstone.SmartClause.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

public class DocumentDto {
    
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class DocumentUploadResponse {
        private String id;
        private String name;
        private Long size;
        private String type;
        private String status;
        
        @JsonProperty("uploaded_at")
        private LocalDateTime uploadedAt;
    }
    
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class DocumentListItem {
        private String id;
        private String name;
        private String status;
        
        @JsonProperty("analysis_summary")
        private String analysisSummary;
    }
    
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class DocumentListResponse {
        private List<DocumentListItem> documents;
    }
    
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class DocumentDetailResponse {
        private String id;
        private String name;
        private byte[] content;
    }
} 