package com.capstone.SmartClause.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

public class ChatDto {
    
    // Request DTOs
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SendMessageRequest {
        private String content;
        
        @JsonProperty("type")
        private String type = "user";
        
        // Constructor to ensure type is always set
        public SendMessageRequest(String content) {
            this.content = content;
            this.type = "user";
        }
        
        // Getter to ensure type is never null
        public String getType() {
            return type != null ? type : "user";
        }
        
        // Setter to validate type
        public void setType(String type) {
            this.type = "user"; // Always force to "user" for security
        }
    }
    
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ChatMemoryConfigRequest {
        @JsonProperty("memory_length")
        private int memoryLength;
    }
    
    // Response DTOs
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class MessageMetadata {
        @JsonProperty("document_references")
        private List<Map<String, Object>> documentReferences;
        
        @JsonProperty("retrieval_context")
        private Map<String, Object> retrievalContext;
        
        @JsonProperty("analysis_context")
        private Map<String, Object> analysisContext;
    }
    
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ChatMessage {
        private String id;
        private String content;
        private String type;
        private OffsetDateTime timestamp;
        private MessageMetadata metadata;
    }
    
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class GetMessagesResponse {
        private List<ChatMessage> messages;
        
        @JsonProperty("total_count")
        private int totalCount;
        
        @JsonProperty("has_more")
        private boolean hasMore;
    }
    
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SendMessageResponse {
        private ChatMessage message;
    }
    
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ChatHealthResponse {
        private String status;
        private String version;
        
        @JsonProperty("database_connected")
        private boolean databaseConnected;
        
        @JsonProperty("analyzer_connected")
        private boolean analyzerConnected;
        
        @JsonProperty("backend_connected")
        private boolean backendConnected;
    }
    
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ChatSessionResponse {
        @JsonProperty("session_id")
        private String sessionId;
        
        @JsonProperty("space_id")
        private String spaceId;
        
        @JsonProperty("memory_length")
        private int memoryLength;
        
        @JsonProperty("created_at")
        private OffsetDateTime createdAt;
        
        @JsonProperty("updated_at")
        private OffsetDateTime updatedAt;
    }
} 