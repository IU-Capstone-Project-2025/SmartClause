package com.capstone.SmartClause.model;

import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.Data;
import java.util.List;

@Data
public class AnalysisResponse {
    @JsonProperty("document_points")
    private List<DocumentPoint> documentPoints;
    
    @JsonProperty("document_id")
    private String documentId;
    
    @JsonProperty("document_metadata")
    private DocumentMetadata documentMetadata;
    
    @JsonProperty("total_points")
    private int totalPoints;
    
    @JsonProperty("analysis_timestamp")
    private String analysisTimestamp;
    
    @JsonProperty("points")
    private List<AnalysisPoint> points;

    public List<DocumentPoint> getDocumentPoints() {
        return documentPoints;
    }

    @Data
    public static class DocumentPoint {
        @JsonProperty("point_number")
        private String pointNumber;
        
        @JsonProperty("point_content")
        private String pointContent;
        
        @JsonProperty("point_type")
        private String pointType;
        
        @JsonProperty("analysis_points")
        private List<AnalysisPoint> analysisPoints;
    }

    @Data
    public static class AnalysisPoint {
        private String cause;
        private String risk;
        private String recommendation;
    }

    public static class DocumentMetadata {
        @JsonProperty("total_length")
        private int totalLength;
        
        @JsonProperty("word_count")
        private int wordCount;
        
        @JsonProperty("paragraph_count")
        private int paragraphCount;
        
        private String title;
    }
}
