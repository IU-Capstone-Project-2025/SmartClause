package com.capstone.SmartClause.service;

import com.capstone.SmartClause.model.Document;
import com.capstone.SmartClause.model.AnalysisResult;
import com.capstone.SmartClause.model.AnalysisResponse;
import com.capstone.SmartClause.model.dto.DocumentDto;
import com.capstone.SmartClause.repository.DocumentRepository;
import com.capstone.SmartClause.repository.AnalysisResultRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Async;
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
import java.util.ArrayList;
import java.util.HashMap;
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
    private ObjectMapper objectMapper;

    // Directory for storing uploaded files
    private final String uploadDir = "uploads/";

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

    public DocumentDto.DocumentUploadResponse uploadDocument(UUID spaceId, MultipartFile file, String name, String userId) throws IOException {
        logger.info("Uploading document to space: {} by user: {}", spaceId, userId);

        // Validate file
        if (file.isEmpty()) {
            throw new IllegalArgumentException("File cannot be empty");
        }

        String fileName = name != null ? name : file.getOriginalFilename();
        
        // Check for duplicate names in space
        if (documentRepository.existsByNameAndSpaceId(fileName, spaceId)) {
            throw new IllegalArgumentException("Document with name '" + fileName + "' already exists in this space");
        }

        // Create upload directory if it doesn't exist
        Path uploadPath = Paths.get(uploadDir);
        if (!Files.exists(uploadPath)) {
            Files.createDirectories(uploadPath);
        }

        // Save file to disk
        String uniqueFileName = UUID.randomUUID().toString() + "_" + file.getOriginalFilename();
        Path filePath = uploadPath.resolve(uniqueFileName);
        Files.copy(file.getInputStream(), filePath);

        // Create document entity
        Document document = new Document();
        document.setName(fileName);
        document.setOriginalFilename(file.getOriginalFilename());
        document.setFilePath(filePath.toString());
        document.setSize(file.getSize());
        document.setContentType(file.getContentType());
        document.setStatus(Document.DocumentStatus.UPLOADING);
        document.setUserId(userId);
        
        // Store the file content as bytes
        document.setContent(file.getBytes());
        
        // Set space relationship
        document.setSpace(new com.capstone.SmartClause.model.Space());
        document.getSpace().setId(spaceId);

        Document savedDocument = documentRepository.save(document);
        logger.info("Uploaded document with ID: {}", savedDocument.getId());

        // Start analysis process asynchronously
        startDocumentAnalysis(savedDocument);

        return convertToDocumentUploadResponse(savedDocument);
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

        Optional<AnalysisResult> analysisOpt = analysisResultRepository.findByDocumentId(document.getAnalysisDocumentId());
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

        Optional<AnalysisResult> analysisOpt = analysisResultRepository.findByDocumentId(document.getAnalysisDocumentId());
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

    public String reanalyzeDocument(UUID documentId) {
        return reanalyzeDocument(documentId, null);
    }

    public String reanalyzeDocument(UUID documentId, String userId) {
        logger.info("Starting reanalysis for document: {} for user: {}", documentId, userId);
        
        Optional<Document> documentOpt = userId != null 
            ? documentRepository.findByIdAndUserId(documentId, userId)
            : documentRepository.findById(documentId);
            
        if (documentOpt.isEmpty()) {
            throw new IllegalArgumentException("Document not found");
        }

        Document document = documentOpt.get();
        
        // Delete existing analysis results if they exist
        if (document.getAnalysisDocumentId() != null) {
            analysisResultRepository.deleteByDocumentId(document.getAnalysisDocumentId());
        }

        // Reset document status and analysis ID
        document.setStatus(Document.DocumentStatus.PROCESSING);
        String newAnalysisDocumentId = UUID.randomUUID().toString();
        document.setAnalysisDocumentId(newAnalysisDocumentId);
        documentRepository.save(document);

        // Start new analysis
        analyzeDocumentAsync(document, newAnalysisDocumentId);
        
        return newAnalysisDocumentId;
    }

    private void startDocumentAnalysis(Document document) {
        try {
            // Update status to processing
            document.setStatus(Document.DocumentStatus.PROCESSING);
            documentRepository.save(document);

            // Generate unique analysis document ID
            String analysisDocumentId = UUID.randomUUID().toString();
            document.setAnalysisDocumentId(analysisDocumentId);
            documentRepository.save(document);

            // Call analyzer microservice asynchronously
            analyzeDocumentAsync(document, analysisDocumentId);

        } catch (Exception e) {
            logger.error("Failed to start analysis for document: {}", document.getId(), e);
            document.setStatus(Document.DocumentStatus.ERROR);
            documentRepository.save(document);
        }
    }

    @Async
    public void analyzeDocumentAsync(Document document, String analysisDocumentId) {
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

            // Call the analyzer microservice
            AnalysisResponse analysisResponse = analysisService.analyzeDocument(analysisDocumentId, multipartFile);
            
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
            // Create AnalysisResult entity
            AnalysisResult analysisResult = new AnalysisResult();
            analysisResult.setDocumentId(analysisDocumentId);
            
            // Use ObjectMapper to convert AnalysisResponse to Map, preserving the exact JSON structure from analyzer
            @SuppressWarnings("unchecked")
            Map<String, Object> analysisPoints = objectMapper.convertValue(analysisResponse, Map.class);
            
            analysisResult.setAnalysisPoints(analysisPoints);
            
            // Save to database
            analysisResultRepository.save(analysisResult);
            logger.info("Analysis results saved for document ID: {} with exact analyzer response structure", analysisDocumentId);
            
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