package com.capstone.SmartClause.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

public class SpaceDto {
    
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class CreateSpaceRequest {
        private String name;
        private String description;
    }
    
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class UpdateSpaceRequest {
        private String name;
        private String description;
    }
    
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SpaceResponse {
        private String id;
        private String name;
        private String description;
        
        @JsonProperty("created_at")
        private LocalDateTime createdAt;
    }
    
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SpaceListItem {
        private String id;
        private String name;
        private String description;
        
        @JsonProperty("created_at")
        private LocalDateTime createdAt;
        
        @JsonProperty("documents_count")
        private int documentsCount;
        
        private String status;
    }
    
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SpaceDetailResponse {
        private String id;
        private String name;
        private String description;
        
        @JsonProperty("created_at")
        private LocalDateTime createdAt;
        
        private List<DocumentDto.DocumentListItem> documents;
    }
    
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SpaceListResponse {
        private List<SpaceListItem> spaces;
    }
} 