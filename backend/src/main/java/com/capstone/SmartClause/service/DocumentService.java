package com.capstone.SmartClause.service;

import com.capstone.SmartClause.model.Document;
import com.capstone.SmartClause.model.AnalysisResult;
import com.capstone.SmartClause.model.AnalysisResponse;
import com.capstone.SmartClause.model.dto.DocumentDto;
import com.capstone.SmartClause.repository.DocumentRepository;
import com.capstone.SmartClause.repository.AnalysisResultRepository;
import com.capstone.SmartClause.repository.SpaceRepository;
import com.capstone.SmartClause.model.Space;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationContext;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@Transactional
public class DocumentService {

    private static final Logger logger = LoggerFactory.getLogger(DocumentService.class);

    @Autowired
    private DocumentRepository documentRepository;

    @Autowired
    private AnalysisResultRepository analysisResultRepository;

    @Autowired
    private AnalysisService analysisService;

    @Autowired
    private SpaceRepository spaceRepository;

    @Autowired
    private ObjectMapper objectMapper;
    
    @Autowired
    private ApplicationContext applicationContext;

    // Directory for storing uploaded files
    private final String uploadDir = "uploads/";
    
    // Cache TTL in hours
    private final int CACHE_TTL_HOURS = 1;

    public List<DocumentDto.DocumentListItem> getDocumentsBySpaceId(UUID spaceId) {
        logger.info("Fetching documents for space: {}", spaceId);
        List<Document> documents = documentRepository.findBySpaceIdOrderByUploadedAtDesc(spaceId);
        
        return documents.stream()
            .map(this::convertToDocumentListItem)
            .collect(Collectors.toList());
    }

    public List<DocumentDto.DocumentListItem> getDocumentsBySpaceId(UUID spaceId, String userId) {
        logger.info("Fetching documents for space: {} and user: {}", spaceId, userId);
        
        // Use repository method that filters by both space and user
        List<Document> documents = documentRepository.findBySpaceIdAndUserIdOrderByUploadedAtDesc(spaceId, userId);
        
        return documents.stream()
            .map(this::convertToDocumentListItem)
            .collect(Collectors.toList());
    }

    public Optional<DocumentDto.DocumentDetailResponse> getDocumentById(UUID documentId) {
        logger.info("Fetching document details for ID: {}", documentId);
        
        Optional<Document> documentOpt = documentRepository.findById(documentId);
        if (documentOpt.isEmpty()) {
            return Optional.empty();
        }

        Document document = documentOpt.get();
        DocumentDto.DocumentDetailResponse response = new DocumentDto.DocumentDetailResponse();
        response.setId(document.getId().toString());
        response.setName(document.getName());
        response.setContent(document.getContent());
        
        // Analysis data is available via separate endpoint: GET /api/documents/{id}/analysis

        return Optional.of(response);
    }

    public Optional<DocumentDto.DocumentDetailResponse> getDocumentById(UUID documentId, String userId) {
        logger.info("Fetching document details for ID: {} and user: {}", documentId, userId);
        
        // First verify the document belongs to the user
        Optional<Document> documentOpt = documentRepository.findByIdAndUserId(documentId, userId);
        if (documentOpt.isEmpty()) {
            return Optional.empty();
        }

        Document document = documentOpt.get();
        DocumentDto.DocumentDetailResponse response = new DocumentDto.DocumentDetailResponse();
        response.setId(document.getId().toString());
        response.setName(document.getName());
        response.setContent(document.getContent());
        
        // Analysis data is available via separate endpoint: GET /api/documents/{id}/analysis

        return Optional.of(response);
    }

    public DocumentDto.DocumentUploadResult uploadDocument(UUID spaceId, MultipartFile file, String userId) throws IOException {
        return uploadDocument(spaceId, file, userId, null);
    }

    public DocumentDto.DocumentUploadResult uploadDocument(UUID spaceId, MultipartFile file, String userId, String authorizationHeader) throws IOException {
        logger.info("Uploading document to space: {} by user: {}", spaceId, userId);

        // Validate space exists
        if (!spaceRepository.existsById(spaceId)) {
            throw new IllegalArgumentException("Space not found");
        }

        // Create uploads directory if it doesn't exist
        Path uploadPath = Paths.get(uploadDir);
        if (!Files.exists(uploadPath)) {
            Files.createDirectories(uploadPath);
        }

        // Generate unique filename
        String originalFilename = file.getOriginalFilename();
        String fileExtension = originalFilename != null && originalFilename.contains(".") 
            ? originalFilename.substring(originalFilename.lastIndexOf(".")) 
            : "";
        String uniqueFilename = UUID.randomUUID() + fileExtension;
        Path filePath = uploadPath.resolve(uniqueFilename);

        // Save file to disk
        Files.copy(file.getInputStream(), filePath);

        // Create document entity
        Document document = new Document();
        document.setName(originalFilename != null ? originalFilename : "Unknown");
        document.setOriginalFilename(originalFilename);
        document.setFilePath(filePath.toString());
        document.setSize(file.getSize());
        document.setContentType(file.getContentType());
        document.setStatus(Document.DocumentStatus.UPLOADING);
        document.setUserId(userId);
        
        // Set space relationship
        Optional<Space> spaceOpt = spaceRepository.findById(spaceId);
        if (spaceOpt.isPresent()) {
            document.setSpace(spaceOpt.get());
        } else {
            throw new IllegalArgumentException("Space not found");
        }

        // Read and store file content
        byte[] fileContent = file.getBytes();
        document.setContent(fileContent);
        
        // Generate content hash for caching and duplicate detection
        String contentHash = generateContentHash(fileContent);
        document.setContentHash(contentHash);
        
        // Check for duplicate document in this space for this user
        Optional<Document> existingDocument = documentRepository.findByContentHashAndSpaceIdAndUserId(
            contentHash, spaceId, userId);
        
        if (existingDocument.isPresent()) {
            logger.info("Duplicate document detected: contentHash={}, spaceId={}, userId={}", 
                contentHash.substring(0, 8) + "...", spaceId, userId);
            
            Document existing = existingDocument.get();
            
            DocumentDto.DocumentDuplicateInfo duplicateInfo = new DocumentDto.DocumentDuplicateInfo();
            duplicateInfo.setExistingDocumentId(existing.getId().toString());
            duplicateInfo.setExistingDocumentName(existing.getName());
            duplicateInfo.setUploadedAt(existing.getUploadedAt());
            duplicateInfo.setAnalysisStatus(existing.getStatus().name().toLowerCase());
            duplicateInfo.setMessage("A document with identical content already exists in this space.");
            
            DocumentDto.DocumentUploadResult result = new DocumentDto.DocumentUploadResult();
            result.setDuplicate(true);
            result.setUploadResponse(null);
            result.setDuplicateInfo(duplicateInfo);
            
            return result;
        }
        
        Document savedDocument = documentRepository.save(document);
        logger.info("Uploaded document with ID: {}", savedDocument.getId());

        // Check for cached analysis before starting new analysis
        boolean cacheHit = checkAndUseCachedAnalysis(savedDocument, userId, contentHash, authorizationHeader);
        if (cacheHit) {
            logger.info("CACHE HIT: Used cached analysis for document: {} (user: {}, hash: {})", 
                savedDocument.getId(), userId, contentHash.substring(0, 8) + "...");
        } else {
            logger.info("CACHE MISS: Starting new analysis for document: {} (user: {}, hash: {})", 
                savedDocument.getId(), userId, contentHash.substring(0, 8) + "...");
            // Start analysis process asynchronously with authorization header
            startDocumentAnalysis(savedDocument, authorizationHeader);
        }

        DocumentDto.DocumentUploadResponse uploadResponse = convertToDocumentUploadResponse(savedDocument);
        
        DocumentDto.DocumentUploadResult result = new DocumentDto.DocumentUploadResult();
        result.setDuplicate(false);
        result.setUploadResponse(uploadResponse);
        result.setDuplicateInfo(null);
        
        return result;
    }

    public Optional<Map<String, Object>> getDocumentAnalysis(UUID documentId) {
        logger.info("Fetching analysis for document: {}", documentId);
        
        Optional<Document> documentOpt = documentRepository.findById(documentId);
        if (documentOpt.isEmpty()) {
            return Optional.empty();
        }

        Document document = documentOpt.get();
        if (document.getAnalysisDocumentId() == null) {
            return Optional.empty();
        }

        Optional<AnalysisResult> analysisOpt = analysisResultRepository.findLatestByDocumentId(document.getAnalysisDocumentId());
        return analysisOpt.map(AnalysisResult::getAnalysisPoints);
    }

    public Optional<Map<String, Object>> getDocumentAnalysis(UUID documentId, String userId) {
        logger.info("Fetching analysis for document: {} and user: {}", documentId, userId);
        
        // First verify the document belongs to the user
        Optional<Document> documentOpt = documentRepository.findByIdAndUserId(documentId, userId);
        if (documentOpt.isEmpty()) {
            return Optional.empty();
        }

        Document document = documentOpt.get();
        if (document.getAnalysisDocumentId() == null) {
            return Optional.empty();
        }

        Optional<AnalysisResult> analysisOpt = analysisResultRepository.findLatestByDocumentId(document.getAnalysisDocumentId());
        return analysisOpt.map(AnalysisResult::getAnalysisPoints);
    }

    public boolean deleteDocument(UUID documentId) {
        return deleteDocument(documentId, null);
    }

    public boolean deleteDocument(UUID documentId, String userId) {
        logger.info("Deleting document: {} for user: {}", documentId, userId);

        Optional<Document> documentOpt = userId != null 
            ? documentRepository.findByIdAndUserId(documentId, userId)
            : documentRepository.findById(documentId);

        if (documentOpt.isEmpty()) {
            return false;
        }

        Document document = documentOpt.get();

        // Delete analysis results if they exist
        if (document.getAnalysisDocumentId() != null) {
            analysisResultRepository.deleteByDocumentId(document.getAnalysisDocumentId());
        }

        // Delete file from disk
        if (document.getFilePath() != null) {
            try {
                Files.deleteIfExists(Paths.get(document.getFilePath()));
            } catch (IOException e) {
                logger.warn("Failed to delete file: {}", document.getFilePath(), e);
            }
        }

        documentRepository.deleteById(documentId);
        logger.info("Deleted document: {}", documentId);
        
        return true;
    }

    public void deleteDocumentsBySpaceId(UUID spaceId) {
        logger.info("Deleting all documents in space: {}", spaceId);
        List<Document> documents = documentRepository.findBySpaceIdOrderByUploadedAtDesc(spaceId);
        
        for (Document document : documents) {
            deleteDocument(document.getId());
        }
    }

    public String reanalyzeDocument(UUID documentId, String userId) {
        return reanalyzeDocument(documentId, userId, null);
    }

    public String reanalyzeDocument(UUID documentId, String userId, String authorizationHeader) {
        logger.info("Starting reanalysis for document: {} for user: {}", documentId, userId);
        
        try {
            Optional<Document> documentOpt = userId != null 
                ? documentRepository.findByIdAndUserId(documentId, userId)
                : documentRepository.findById(documentId);
                
            if (documentOpt.isEmpty()) {
                logger.error("Document not found for reanalysis: documentId={}, userId={}", documentId, userId);
                throw new IllegalArgumentException("Document not found");
            }

            Document document = documentOpt.get();
            logger.info("Found document for reanalysis: {}", document.getId());
            
            // Delete existing analysis results if they exist
            if (document.getAnalysisDocumentId() != null) {
                logger.info("Deleting existing analysis results for document: {}", document.getAnalysisDocumentId());
                try {
                    analysisResultRepository.deleteByDocumentId(document.getAnalysisDocumentId());
                    logger.info("Successfully deleted existing analysis results");
                } catch (Exception e) {
                    logger.error("Error deleting existing analysis results: {}", e.getMessage(), e);
                    // Continue with reanalysis even if deletion fails
                }
            }

            // Reset document status and analysis ID
            document.setStatus(Document.DocumentStatus.PROCESSING);
            String newAnalysisDocumentId = UUID.randomUUID().toString();
            document.setAnalysisDocumentId(newAnalysisDocumentId);
            logger.info("Generated new analysis document ID: {}", newAnalysisDocumentId);
            
            try {
                documentRepository.save(document);
                logger.info("Successfully saved document with new analysis ID");
            } catch (Exception e) {
                logger.error("Error saving document during reanalysis: {}", e.getMessage(), e);
                throw new RuntimeException("Failed to update document for reanalysis", e);
            }

            // Start new analysis with authorization header (bypass cache for reanalysis)
            try {
                // Get the Spring proxy to ensure @Async works properly
                DocumentService self = applicationContext.getBean(DocumentService.class);
                self.analyzeDocumentAsync(document, newAnalysisDocumentId, authorizationHeader, true);
                logger.info("Successfully started async reanalysis for document: {}", documentId);
            } catch (Exception e) {
                logger.error("Error starting async reanalysis: {}", e.getMessage(), e);
                throw new RuntimeException("Failed to start reanalysis", e);
            }
            
            return newAnalysisDocumentId;
        } catch (Exception e) {
            logger.error("Reanalysis failed for document: {} for user: {}", documentId, userId, e);
            throw e; // Re-throw to be handled by controller
        }
    }

    public byte[] exportDocumentAnalysisPdf(UUID documentId, String userId) {
        return exportDocumentAnalysisPdf(documentId, userId, null);
    }

    public byte[] exportDocumentAnalysisPdf(UUID documentId, String userId, String authorizationHeader) {
        logger.info("Exporting analysis PDF for document: {} and user: {}", documentId, userId);
        
        // First verify the document belongs to the user
        Optional<Document> documentOpt = userId != null 
            ? documentRepository.findByIdAndUserId(documentId, userId)
            : documentRepository.findById(documentId);
            
        if (documentOpt.isEmpty()) {
            throw new IllegalArgumentException("Document not found");
        }

        Document document = documentOpt.get();
        
        // Check if document has analysis results
        if (document.getAnalysisDocumentId() == null) {
            throw new IllegalArgumentException("No analysis found for this document");
        }
        
        // Verify analysis exists in database
        Optional<AnalysisResult> analysisOpt = analysisResultRepository.findLatestByDocumentId(document.getAnalysisDocumentId());
        if (analysisOpt.isEmpty()) {
            throw new IllegalArgumentException("Analysis not found for this document");
        }

        try {
            // Call analyzer service to export PDF with authorization header
            byte[] pdfBytes = analysisService.exportAnalysisPdf(document.getAnalysisDocumentId(), authorizationHeader);
            logger.info("PDF export completed for document: {}", documentId);
            return pdfBytes;
        } catch (Exception e) {
            logger.error("Failed to export PDF for document: {}", documentId, e);
            throw new RuntimeException("Failed to export analysis PDF: " + e.getMessage(), e);
        }
    }

    private void startDocumentAnalysis(Document document) {
        startDocumentAnalysis(document, null);
    }

    private void startDocumentAnalysis(Document document, String authorizationHeader) {
        try {
            // Update status to processing
            document.setStatus(Document.DocumentStatus.PROCESSING);
            documentRepository.save(document);

            // Generate unique analysis document ID
            String analysisDocumentId = UUID.randomUUID().toString();
            document.setAnalysisDocumentId(analysisDocumentId);
            documentRepository.save(document);

            // Call analyzer microservice asynchronously (normal upload, use cache)
            // Get the Spring proxy to ensure @Async works properly
            DocumentService self = applicationContext.getBean(DocumentService.class);
            self.analyzeDocumentAsync(document, analysisDocumentId, authorizationHeader, false);

        } catch (Exception e) {
            logger.error("Failed to start analysis for document: {}", document.getId(), e);
            document.setStatus(Document.DocumentStatus.ERROR);
            documentRepository.save(document);
        }
    }

    @Async("taskExecutor")
    public void analyzeDocumentAsync(Document document, String analysisDocumentId) {
        analyzeDocumentAsync(document, analysisDocumentId, null, false);
    }

    @Async("taskExecutor")
    public void analyzeDocumentAsync(Document document, String analysisDocumentId, String authorizationHeader) {
        analyzeDocumentAsync(document, analysisDocumentId, authorizationHeader, false);
    }
    
    @Async("taskExecutor")
    public void analyzeDocumentAsync(Document document, String analysisDocumentId, String authorizationHeader, boolean bypassCache) {
        try {
            logger.info("Starting async analysis for document: {} with analysis ID: {}", document.getId(), analysisDocumentId);

            // Create a MultipartFile from the saved file for the analyzer
            Path filePath = Paths.get(document.getFilePath());
            byte[] fileBytes = Files.readAllBytes(filePath);
            
            MultipartFile multipartFile = new CustomMultipartFile(
                document.getOriginalFilename(),
                document.getContentType(),
                fileBytes
            );

            // Call the analyzer microservice (with cache bypass flag for reanalysis)
            AnalysisResponse analysisResponse = analysisService.analyzeDocument(analysisDocumentId, multipartFile, authorizationHeader, bypassCache);
            
            if (analysisResponse != null) {
                logger.info("Analysis completed successfully for document: {}", document.getId());
                
                // Save analysis results to the database
                saveAnalysisResults(analysisDocumentId, analysisResponse);
                
                document.setStatus(Document.DocumentStatus.COMPLETED);
            } else {
                logger.warn("Analysis returned null response for document: {}", document.getId());
                document.setStatus(Document.DocumentStatus.ERROR);
            }

        } catch (Exception e) {
            logger.error("Analysis failed for document: {}", document.getId(), e);
            document.setStatus(Document.DocumentStatus.ERROR);
        } finally {
            // Always save the final status
            documentRepository.save(document);
        }
    }

    private void saveAnalysisResults(String analysisDocumentId, AnalysisResponse analysisResponse) {
        try {
            // Find the document to get content hash and user info
            Optional<Document> documentOpt = documentRepository.findByAnalysisDocumentId(analysisDocumentId);
            if (documentOpt.isEmpty()) {
                logger.warn("Could not find document for analysis ID: {}", analysisDocumentId);
                return;
            }
            
            Document document = documentOpt.get();
            
            // Create AnalysisResult entity with caching information
            AnalysisResult analysisResult = new AnalysisResult();
            analysisResult.setDocumentId(analysisDocumentId);
            analysisResult.setUserId(document.getUserId());
            analysisResult.setContentHash(document.getContentHash());
            analysisResult.setExpiresAt(LocalDateTime.now().plusHours(CACHE_TTL_HOURS));
            
            // Use ObjectMapper to convert AnalysisResponse to Map, preserving the exact JSON structure from analyzer
            @SuppressWarnings("unchecked")
            Map<String, Object> analysisPoints = objectMapper.convertValue(analysisResponse, Map.class);
            
            analysisResult.setAnalysisPoints(analysisPoints);
            
            // Save to database
            analysisResultRepository.save(analysisResult);
            logger.info("Analysis results saved for document ID: {} with caching info (contentHash: {}, userId: {}, expires: {})", 
                analysisDocumentId, document.getContentHash(), document.getUserId(), analysisResult.getExpiresAt());
            
        } catch (Exception e) {
            logger.error("Failed to save analysis results for document ID: {}", analysisDocumentId, e);
        }
    }

    private DocumentDto.DocumentListItem convertToDocumentListItem(Document document) {
        DocumentDto.DocumentListItem item = new DocumentDto.DocumentListItem();
        item.setId(document.getId().toString());
        item.setName(document.getName());
        item.setStatus(document.getStatus().name().toLowerCase());
        item.setAnalysisSummary(generateAnalysisSummary(document));
        return item;
    }

    private DocumentDto.DocumentUploadResponse convertToDocumentUploadResponse(Document document) {
        DocumentDto.DocumentUploadResponse response = new DocumentDto.DocumentUploadResponse();
        response.setId(document.getId().toString());
        response.setName(document.getName());
        response.setSize(document.getSize());
        response.setType(document.getContentType());
        response.setStatus(document.getStatus().name().toLowerCase());
        response.setUploadedAt(document.getUploadedAt());
        return response;
    }



    private String generateAnalysisSummary(Document document) {
        if (document.getStatus() == Document.DocumentStatus.COMPLETED) {
            return "Analysis completed - Found potential issues";
        } else if (document.getStatus() == Document.DocumentStatus.PROCESSING) {
            return "Analysis in progress...";
        } else if (document.getStatus() == Document.DocumentStatus.ERROR) {
            return "Analysis failed";
        }
        return "Pending analysis";
    }
    
    // === CACHING UTILITIES ===
    
    /**
     * Generate SHA-256 hash of document content for caching and duplicate detection
     */
    private String generateContentHash(byte[] content) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(content);
            return HexFormat.of().formatHex(hash);
        } catch (NoSuchAlgorithmException e) {
            logger.error("SHA-256 algorithm not available", e);
            // Fallback to simpler hash
            return String.valueOf(content.hashCode());
        }
    }
    
    /**
     * Check for cached analysis and use it if available
     * @param document The document being processed
     * @param userId User ID for cache lookup
     * @param contentHash Content hash for cache lookup
     * @param authorizationHeader Authorization header (for logging)
     * @return true if cached analysis was used, false if new analysis needed
     */
    private boolean checkAndUseCachedAnalysis(Document document, String userId, String contentHash, String authorizationHeader) {
        try {
            LocalDateTime now = LocalDateTime.now();
            Optional<AnalysisResult> cachedResult = analysisResultRepository.findCachedAnalysis(contentHash, userId, now);
            
            if (cachedResult.isPresent()) {
                logger.info("Found cached analysis for contentHash: {} and user: {}", contentHash, userId);
                
                // Generate new analysis document ID for this document
                String analysisDocumentId = UUID.randomUUID().toString();
                document.setAnalysisDocumentId(analysisDocumentId);
                document.setStatus(Document.DocumentStatus.COMPLETED);
                documentRepository.save(document);
                
                // Create new analysis result entry based on cached data
                AnalysisResult newAnalysisResult = new AnalysisResult();
                newAnalysisResult.setDocumentId(analysisDocumentId);
                newAnalysisResult.setUserId(userId);
                newAnalysisResult.setContentHash(contentHash);
                newAnalysisResult.setAnalysisPoints(cachedResult.get().getAnalysisPoints());
                newAnalysisResult.setExpiresAt(now.plusHours(CACHE_TTL_HOURS));
                
                analysisResultRepository.save(newAnalysisResult);
                
                long cacheAgeMinutes = java.time.Duration.between(cachedResult.get().getCreatedAt(), now).toMinutes();
                logger.info("CACHE REUSE: Analysis for document: {} (cache age: {} minutes, saved analysis time)", 
                    document.getId(), cacheAgeMinutes);
                
                return true;
            }
            
            logger.debug("CACHE MISS: No cached analysis found for contentHash: {} and user: {}", 
                contentHash.substring(0, 8) + "...", userId);
            return false;
            
        } catch (Exception e) {
            logger.error("Error checking cached analysis for document: " + document.getId(), e);
            // On error, proceed with normal analysis
            return false;
                 }
     }
     
         /**
      * Scheduled task to clean up expired cache entries
      * Runs every hour to remove expired analysis results
      */
    @Scheduled(fixedRate = 3600000) // Run every hour (3600000 ms)
    public void cleanupExpiredCacheEntries() {
        try {
            LocalDateTime now = LocalDateTime.now();
            int deletedCount = analysisResultRepository.deleteExpiredCacheEntries(now);
            
            if (deletedCount > 0) {
                logger.info("Cache cleanup: Removed {} expired analysis results", deletedCount);
            } else {
                logger.debug("Cache cleanup: No expired entries found");
            }
            
            // Log cache statistics
            long activeCacheEntries = analysisResultRepository.countActiveCacheEntries(now);
            logger.debug("Cache statistics: {} active cache entries", activeCacheEntries);
            
        } catch (Exception e) {
            logger.error("Failed to cleanup expired cache entries", e);
        }
    }
    
    /**
     * Get cache statistics for monitoring
     * @param userId Optional user ID to get user-specific stats
     * @return Map containing cache statistics
     */
    public Map<String, Object> getCacheStatistics(String userId) {
        Map<String, Object> stats = new HashMap<>();
        LocalDateTime now = LocalDateTime.now();
        
        try {
            long totalActiveCacheEntries = analysisResultRepository.countActiveCacheEntries(now);
            stats.put("total_active_cache_entries", totalActiveCacheEntries);
            stats.put("cache_ttl_hours", CACHE_TTL_HOURS);
            stats.put("timestamp", now.toString());
            
            if (userId != null) {
                long userCacheEntries = analysisResultRepository.countActiveCacheEntriesForUser(userId, now);
                stats.put("user_cache_entries", userCacheEntries);
                stats.put("user_id", userId);
            }
            
            logger.debug("Cache statistics generated: {}", stats);
            
        } catch (Exception e) {
            logger.error("Failed to generate cache statistics", e);
            stats.put("error", "Failed to retrieve cache statistics");
        }
        
        return stats;
    }

    // Custom MultipartFile implementation for internal use
    private static class CustomMultipartFile implements MultipartFile {
        private final String name;
        private final String contentType;
        private final byte[] bytes;

        public CustomMultipartFile(String name, String contentType, byte[] bytes) {
            this.name = name;
            this.contentType = contentType;
            this.bytes = bytes;
        }

        @Override
        public String getName() {
            return "file";
        }

        @Override
        public String getOriginalFilename() {
            return name;
        }

        @Override
        public String getContentType() {
            return contentType;
        }

        @Override
        public boolean isEmpty() {
            return bytes.length == 0;
        }

        @Override
        public long getSize() {
            return bytes.length;
        }

        @Override
        public byte[] getBytes() throws IOException {
            return bytes;
        }

        @Override
        public InputStream getInputStream() throws IOException {
            return new ByteArrayInputStream(bytes);
        }

        @Override
        public void transferTo(File dest) throws IOException, IllegalStateException {
            Files.write(dest.toPath(), bytes);
        }
    }
} 