package com.capstone.SmartClause.controller;

import com.capstone.SmartClause.model.AnalysisResponse;
import com.capstone.SmartClause.service.AnalysisService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.scheduling.annotation.EnableAsync;
import java.util.Map;

@RestController
@RequestMapping("/api/v1")
@EnableAsync
public class Controller {
    
    @Autowired
    private AnalysisService analysisService;

    @PostMapping("/upload")
    public ResponseEntity<?> uploadDocumentFile(
            @RequestParam("id") String id,
            @RequestParam("bytes") MultipartFile file) {
        
        try {
            AnalysisResponse response = analysisService.analyzeDocument(id, file);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to process file: " + e.getMessage()));
        }
    }
}
