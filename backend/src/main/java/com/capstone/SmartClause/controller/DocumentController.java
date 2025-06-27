package com.capstone.SmartClause.controller;

import com.capstone.SmartClause.model.dto.DocumentDto;
import com.capstone.SmartClause.service.DocumentService;
import com.capstone.SmartClause.util.AuthUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.media.Encoding;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*", methods = {RequestMethod.GET, RequestMethod.POST, RequestMethod.PUT, RequestMethod.DELETE}, maxAge = 3600)
@Tag(name = "Documents API", description = "API for managing documents and analysis")
public class DocumentController {

    @Autowired
    private DocumentService documentService;
    
    @Autowired
    private AuthUtils authUtils;

    @Operation(summary = "Upload document to space", description = "Uploads a document file to a specific space")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "201", description = "Document uploaded successfully",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = DocumentDto.DocumentUploadResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid request data",
                content = @Content(mediaType = "application/json"))
    })
    @PostMapping(value = "/spaces/{spaceId}/documents", consumes = "multipart/form-data")
    public ResponseEntity<?> uploadDocument(
            @Parameter(description = "Authorization header") @RequestHeader(value = "Authorization", required = false) String authorization,
            @Parameter(description = "Space ID") @PathVariable String spaceId,
            @Parameter(description = "Binary file data (multipart/form-data)", 
                      content = @Content(mediaType = "application/octet-stream"),
                      schema = @Schema(type = "string", format = "binary")) 
            @RequestParam("file") MultipartFile file,
            @Parameter(description = "Document name (optional)") @RequestParam(value = "name", required = false) String name) {
        
        try {
            UUID spaceUuid = UUID.fromString(spaceId);
            
            if (file.isEmpty()) {
                return ResponseEntity.badRequest()
                    .body(Map.of("error", "File cannot be empty"));
            }

            // Extract user ID from authorization header
            String userId = authUtils.extractUserIdFromHeader(authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }
            
            DocumentDto.DocumentUploadResponse document = documentService.uploadDocument(spaceUuid, file, name, userId);
            
            return ResponseEntity.status(HttpStatus.CREATED)
                .body(Map.of("document", document));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to upload document: " + e.getMessage()));
        }
    }

    @Operation(summary = "Get all documents in space", description = "Retrieves all documents in a specific space")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Documents retrieved successfully",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = DocumentDto.DocumentListResponse.class)))
    })
    @GetMapping("/spaces/{spaceId}/documents")
    public ResponseEntity<?> getDocumentsInSpace(
            @Parameter(description = "Authorization header") @RequestHeader(value = "Authorization", required = false) String authorization,
            @Parameter(description = "Space ID") @PathVariable String spaceId) {
        
        try {
            UUID spaceUuid = UUID.fromString(spaceId);
            
            // Extract user ID from authorization header
            String userId = authUtils.extractUserIdFromHeader(authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }
            
            List<DocumentDto.DocumentListItem> documents = documentService.getDocumentsBySpaceId(spaceUuid, userId);
            
            DocumentDto.DocumentListResponse response = new DocumentDto.DocumentListResponse();
            response.setDocuments(documents);
            
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", "Invalid space ID format"));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to retrieve documents"));
        }
    }

    @Operation(summary = "Get document details", description = "Retrieves detailed information about a specific document")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Document details retrieved successfully",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = DocumentDto.DocumentDetailResponse.class))),
        @ApiResponse(responseCode = "404", description = "Document not found",
                content = @Content(mediaType = "application/json"))
    })
    @GetMapping("/documents/{documentId}")
    public ResponseEntity<?> getDocumentDetails(
            @Parameter(description = "Authorization header") @RequestHeader(value = "Authorization", required = false) String authorization,
            @Parameter(description = "Document ID") @PathVariable String documentId) {
        
        try {
            UUID documentUuid = UUID.fromString(documentId);
            
            // Extract user ID from authorization header
            String userId = authUtils.extractUserIdFromHeader(authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }
            
            Optional<DocumentDto.DocumentDetailResponse> documentOpt = documentService.getDocumentById(documentUuid, userId);
            
            if (documentOpt.isEmpty()) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(Map.of("error", "Document not found"));
            }
            
            return ResponseEntity.ok(Map.of("document", documentOpt.get()));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", "Invalid document ID format"));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to retrieve document details"));
        }
    }

    @Operation(summary = "Delete document", description = "Deletes a document and its analysis results")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "204", description = "Document deleted successfully"),
        @ApiResponse(responseCode = "404", description = "Document not found",
                content = @Content(mediaType = "application/json"))
    })
    @DeleteMapping("/documents/{documentId}")
    public ResponseEntity<?> deleteDocument(
            @Parameter(description = "Authorization header") @RequestHeader(value = "Authorization", required = false) String authorization,
            @Parameter(description = "Document ID") @PathVariable String documentId) {
        
        try {
            UUID documentUuid = UUID.fromString(documentId);
            
            // Extract user ID from authorization header
            String userId = authUtils.extractUserIdFromHeader(authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }
            
            boolean deleted = documentService.deleteDocument(documentUuid, userId);
            
            if (!deleted) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(Map.of("error", "Document not found"));
            }
            
            return ResponseEntity.noContent().build();
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", "Invalid document ID format"));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to delete document"));
        }
    }

    @Operation(summary = "Get document analysis results", description = "Retrieves analysis results for a specific document exactly as returned by the analyzer microservice")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Analysis results retrieved successfully",
                content = @Content(mediaType = "application/json")),
        @ApiResponse(responseCode = "404", description = "Document or analysis not found",
                content = @Content(mediaType = "application/json"))
    })
    @GetMapping("/documents/{documentId}/analysis")
    public ResponseEntity<?> getDocumentAnalysis(
            @Parameter(description = "Authorization header") @RequestHeader(value = "Authorization", required = false) String authorization,
            @Parameter(description = "Document ID") @PathVariable String documentId) {
        
        try {
            UUID documentUuid = UUID.fromString(documentId);
            
            // Extract user ID from authorization header
            String userId = authUtils.extractUserIdFromHeader(authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }
            
            Optional<Map<String, Object>> analysisOpt = documentService.getDocumentAnalysis(documentUuid, userId);
            
            if (analysisOpt.isEmpty()) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(Map.of("error", "Analysis not found for this document"));
            }
            
            // Return the analysis JSON exactly as stored from analyzer
            return ResponseEntity.ok(analysisOpt.get());
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", "Invalid document ID format"));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to retrieve analysis results"));
        }
    }

    @Operation(summary = "Trigger document reanalysis", description = "Starts a new analysis process for the document")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "202", description = "Analysis started successfully",
                content = @Content(mediaType = "application/json")),
        @ApiResponse(responseCode = "404", description = "Document not found",
                content = @Content(mediaType = "application/json"))
    })
    @PostMapping("/documents/{documentId}/reanalyze")
    public ResponseEntity<?> reanalyzeDocument(
            @Parameter(description = "Authorization header") @RequestHeader(value = "Authorization", required = false) String authorization,
            @Parameter(description = "Document ID") @PathVariable String documentId) {
        
        try {
            UUID documentUuid = UUID.fromString(documentId);
            
            // Extract user ID from authorization header
            String userId = authUtils.extractUserIdFromHeader(authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }
            
            String analysisId = documentService.reanalyzeDocument(documentUuid, userId);
            
            return ResponseEntity.accepted()
                .body(Map.of(
                    "message", "Analysis started",
                    "analysis_id", analysisId
                ));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to start reanalysis"));
        }
    }
} 