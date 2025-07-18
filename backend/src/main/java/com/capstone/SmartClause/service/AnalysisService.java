package com.capstone.SmartClause.service;

import com.capstone.SmartClause.model.AnalysisResponse;
import com.capstone.SmartClause.model.AnalysisResult;
import com.capstone.SmartClause.repository.AnalysisResultRepository;
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
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.LocalDateTime;
import java.util.HexFormat;
import java.util.Map;
import java.util.Optional;

@Service
public class AnalysisService {

    private static final Logger logger = LoggerFactory.getLogger(AnalysisService.class);

    @Value("${analyzer.api.baseUrl}")
    private String analyzerApiUrl;

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private JwtService jwtService;
    
    @Autowired
    private AnalysisResultRepository analysisResultRepository;
    
    // Constants for caching
    private static final String ANONYMOUS_USER_ID = "anonymous";
    private final int CACHE_TTL_HOURS = 1;

    public AnalysisResponse analyzeDocument(String id, MultipartFile file) throws IOException {
        return analyzeDocument(id, file, null);
    }

    public AnalysisResponse analyzeDocument(String id, MultipartFile file, String authorizationHeader) throws IOException {
        logger.info("Sending document for analysis: id={}, filename={}", id, file.getOriginalFilename());
        logger.info("Received authorization header: {}", authorizationHeader != null ? "[PRESENT]" : "[NULL]");

        // Generate content hash for caching
        byte[] fileContent = file.getBytes();
        String contentHash = generateContentHash(fileContent);
        
        // Determine user ID for caching (anonymous for landing page users)
        String userId = determineUserIdForCaching(authorizationHeader);
        
        // Check cache before expensive analysis
        Optional<AnalysisResult> cachedResult = checkCachedAnalysis(contentHash, userId);
        if (cachedResult.isPresent()) {
            logger.info("CACHE HIT: Returning cached analysis for hash: {} (user: {})", 
                contentHash.substring(0, 8) + "...", userId);
            return convertCachedResultToAnalysisResponse(cachedResult.get());
        }
        
        logger.info("CACHE MISS: Starting new analysis for hash: {} (user: {})", 
            contentHash.substring(0, 8) + "...", userId);

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
            AnalysisResponse analysisResponse = response.getBody();
            
            // Save to cache for future requests
            if (analysisResponse != null) {
                saveToCacheAsync(id, userId, contentHash, analysisResponse);
            }
            
            return analysisResponse;
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
    
    // === CACHING UTILITIES ===
    
    /**
     * Generate SHA-256 hash of document content for caching
     */
    private String generateContentHash(byte[] content) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(content);
            return HexFormat.of().formatHex(hash);
        } catch (NoSuchAlgorithmException e) {
            logger.error("SHA-256 algorithm not available", e);
            return String.valueOf(content.hashCode());
        }
    }
    
    /**
     * Determine user ID for caching purposes
     */
    private String determineUserIdForCaching(String authorizationHeader) {
        if (authorizationHeader == null || authorizationHeader.trim().isEmpty()) {
            return ANONYMOUS_USER_ID;
        }
        
        // For authenticated users, we could extract the user ID from token
        // For now, we'll use "authenticated" to separate from anonymous
        // In future, could decode JWT to get actual user ID
        return "authenticated";
    }
    
    /**
     * Check for cached analysis result
     */
    private Optional<AnalysisResult> checkCachedAnalysis(String contentHash, String userId) {
        try {
            LocalDateTime now = LocalDateTime.now();
            return analysisResultRepository.findCachedAnalysis(contentHash, userId, now);
        } catch (Exception e) {
            logger.error("Error checking cache for hash: " + contentHash, e);
            return Optional.empty();
        }
    }
    
    /**
     * Convert cached AnalysisResult to AnalysisResponse
     */
    @SuppressWarnings("unchecked")
    private AnalysisResponse convertCachedResultToAnalysisResponse(AnalysisResult cachedResult) {
        try {
            // The analysis_points field contains the full AnalysisResponse as Map
            Map<String, Object> analysisPoints = cachedResult.getAnalysisPoints();
            
            // Use ObjectMapper to convert Map back to AnalysisResponse
            com.fasterxml.jackson.databind.ObjectMapper objectMapper = new com.fasterxml.jackson.databind.ObjectMapper();
            return objectMapper.convertValue(analysisPoints, AnalysisResponse.class);
            
        } catch (Exception e) {
            logger.error("Error converting cached result to AnalysisResponse", e);
            throw new RuntimeException("Failed to convert cached analysis result", e);
        }
    }
    
    /**
     * Save analysis result to cache asynchronously
     */
    private void saveToCacheAsync(String documentId, String userId, String contentHash, AnalysisResponse analysisResponse) {
        try {
            AnalysisResult cacheEntry = new AnalysisResult();
            cacheEntry.setDocumentId(documentId);
            cacheEntry.setUserId(userId);
            cacheEntry.setContentHash(contentHash);
            cacheEntry.setExpiresAt(LocalDateTime.now().plusHours(CACHE_TTL_HOURS));
            
            // Convert AnalysisResponse to Map for storage
            com.fasterxml.jackson.databind.ObjectMapper objectMapper = new com.fasterxml.jackson.databind.ObjectMapper();
            @SuppressWarnings("unchecked")
            Map<String, Object> analysisPoints = objectMapper.convertValue(analysisResponse, Map.class);
            cacheEntry.setAnalysisPoints(analysisPoints);
            
            analysisResultRepository.save(cacheEntry);
            logger.info("Saved analysis to cache: documentId={}, userId={}, contentHash={}...", 
                documentId, userId, contentHash.substring(0, 8));
                
        } catch (Exception e) {
            logger.error("Failed to save analysis to cache: " + e.getMessage(), e);
            // Don't fail the main request if caching fails
        }
    }
}
