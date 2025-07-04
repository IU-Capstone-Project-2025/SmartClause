package com.capstone.SmartClause.controller;

import com.capstone.SmartClause.model.AnalysisResponse;
import com.capstone.SmartClause.service.AnalysisService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.GetMapping;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;

import java.util.Map;

@RestController
@RequestMapping("/api/v1")
@CrossOrigin(origins = "*", methods = {RequestMethod.GET, RequestMethod.POST, RequestMethod.PUT, RequestMethod.DELETE}, maxAge = 3600)
@Tag(name = "Document Analysis API", description = "API for analyzing legal documents")
public class Controller {
    
    @Autowired
    private AnalysisService analysisService;

    @Operation(summary = "Upload and analyze a document", description = "Uploads a document file and returns analysis results")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Document analyzed successfully",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = AnalysisResponse.class))),
        @ApiResponse(responseCode = "500", description = "Error processing the document",
                content = @Content(mediaType = "application/json"))
    })
    @PostMapping("/get_analysis")
    public ResponseEntity<?> uploadDocumentFile(
            @Parameter(description = "Document identifier") @RequestParam("id") String id,
            @Parameter(description = "Document file") @RequestParam("bytes") MultipartFile file) {
        
        try {
            AnalysisResponse response = analysisService.analyzeDocument(id, file);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to process file: " + e.getMessage()));
        }
    }
    
    @Operation(summary = "Check service health", description = "Returns the health status of the service")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Service is healthy",
                content = @Content(mediaType = "application/json"))
    })
    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> healthCheck() {
        return ResponseEntity.ok(Map.of(
            "status", "UP",
            "service", "SmartClause API",
            "timestamp", java.time.Instant.now().toString()
        ));
    }
}
