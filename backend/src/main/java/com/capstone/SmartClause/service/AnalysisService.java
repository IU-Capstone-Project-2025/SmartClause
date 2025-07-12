package com.capstone.SmartClause.service;

import com.capstone.SmartClause.model.AnalysisResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

@Service
public class AnalysisService {

    private static final Logger logger = LoggerFactory.getLogger(AnalysisService.class);

    @Value("${analyzer.api.baseUrl}")
    private String analyzerApiUrl;

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private JwtService jwtService;

    public AnalysisResponse analyzeDocument(String id, MultipartFile file) throws IOException {
        return analyzeDocument(id, file, null);
    }

    public AnalysisResponse analyzeDocument(String id, MultipartFile file, String authorizationHeader) throws IOException {
        logger.info("Sending document for analysis: id={}, filename={}", id, file.getOriginalFilename());
        logger.info("Received authorization header: {}", authorizationHeader != null ? "[PRESENT]" : "[NULL]");

        String analyzeUrl = analyzerApiUrl + "/analyze";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        
        // Determine which authorization to use
        String effectiveAuthorization = authorizationHeader;
        
        // If no valid user authentication provided, use system account for internal service communication
        if (authorizationHeader == null || authorizationHeader.trim().isEmpty()) {
            logger.info("No user authorization provided - generating system token for public request");
            String systemToken = jwtService.generateSystemToken();
            effectiveAuthorization = "Bearer " + systemToken;
            logger.info("Generated system token for public request: {}...", systemToken.substring(0, Math.min(50, systemToken.length())));
            logger.debug("Using system token for public request to analyzer service");
        } else {
            logger.info("Using provided user authentication for analyzer request");
        }
        
        // Always add authorization header (either user or system)
        headers.set("Authorization", effectiveAuthorization);
        logger.info("Sending Authorization header to analyzer: {}...", effectiveAuthorization.substring(0, Math.min(20, effectiveAuthorization.length())));

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("id", id);
        body.add("file", new org.springframework.core.io.ByteArrayResource(file.getBytes()) {
            @Override
            public String getFilename() {
                return file.getOriginalFilename();
            }
        });

        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

        try {
            ResponseEntity<AnalysisResponse> response = restTemplate.exchange(
                    analyzeUrl,
                    HttpMethod.POST,
                    requestEntity,
                    AnalysisResponse.class
            );

            logger.info("Analysis completed successfully for document: {}", id);
            return response.getBody();
        } catch (Exception e) {
            logger.error("Error during document analysis: {}", e.getMessage(), e);
            throw new RuntimeException("Failed to process document: " + e.getMessage(), e);
        }
    }

    public byte[] exportAnalysisPdf(String documentId) {
        return exportAnalysisPdf(documentId, null);
    }

    public byte[] exportAnalysisPdf(String documentId, String authorizationHeader) {
        logger.info("Exporting analysis as PDF for document: {}", documentId);

        String exportUrl = analyzerApiUrl + "/export/" + documentId + "/pdf";

        HttpHeaders headers = new HttpHeaders();
        headers.setAccept(MediaType.parseMediaTypes("application/pdf"));
        
        // Determine which authorization to use
        String effectiveAuthorization = authorizationHeader;
        
        // If no valid user authentication provided, use system account for internal service communication
        if (authorizationHeader == null || authorizationHeader.trim().isEmpty()) {
            String systemToken = jwtService.generateSystemToken();
            effectiveAuthorization = "Bearer " + systemToken;
            logger.debug("Using system token for public PDF export request to analyzer service");
        } else {
            logger.debug("Using provided user authentication for analyzer PDF export request");
        }
        
        // Always add authorization header (either user or system)
        headers.set("Authorization", effectiveAuthorization);

        HttpEntity<?> requestEntity = new HttpEntity<>(headers);

        try {
            ResponseEntity<byte[]> response = restTemplate.exchange(
                    exportUrl,
                    HttpMethod.GET,
                    requestEntity,
                    byte[].class
            );

            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                logger.info("PDF export completed successfully for document: {}", documentId);
                return response.getBody();
            } else {
                logger.error("PDF export failed for document: {}, status: {}", documentId, response.getStatusCode());
                throw new RuntimeException("Failed to export PDF: Analyzer service returned " + response.getStatusCode());
            }
        } catch (Exception e) {
            logger.error("Error during PDF export for document {}: {}", documentId, e.getMessage(), e);
            throw new RuntimeException("Failed to export PDF: " + e.getMessage(), e);
        }
    }
}
