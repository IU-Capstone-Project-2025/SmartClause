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

import jakarta.servlet.http.HttpServletRequest;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import java.io.IOException;

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
    @PostMapping("/spaces/{spaceId}/documents")
    public ResponseEntity<?> uploadDocument(
            HttpServletRequest request,
            @Parameter(description = "Space ID") @PathVariable String spaceId,
            @Parameter(description = "Document file") @RequestParam("file") MultipartFile file) {
        
        try {
            UUID spaceUuid = UUID.fromString(spaceId);
            
            // Extract user ID from cookies or authorization header
            String userId = authUtils.extractUserIdFromRequest(request, null);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }
            
            // For backward compatibility, try to get authorization token for service communication
            String authToken = authUtils.extractTokenFromCookie(request);
            if (authToken != null) {
                authToken = "Bearer " + authToken;
            }
            
            DocumentDto.DocumentUploadResponse response = documentService.uploadDocument(spaceUuid, file, userId, authToken);
            
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", e.getMessage()));
        } catch (IOException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to upload document"));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to upload document"));
        }
    }

    @Operation(summary = "Get all documents in space", description = "Retrieves all documents in a specific space")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Documents retrieved successfully",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = DocumentDto.DocumentListResponse.class)))
    })
    @GetMapping("/spaces/{spaceId}/documents")
    public ResponseEntity<?> getDocumentsInSpace(
            HttpServletRequest request,
            @Parameter(description = "Space ID") @PathVariable String spaceId,
            @Parameter(description = "Authorization header (optional, will try cookies first)") @RequestHeader(value = "Authorization", required = false) String authorization) {
        
        try {
            UUID spaceUuid = UUID.fromString(spaceId);
            
            // Extract user ID from cookies or authorization header
            String userId = authUtils.extractUserIdFromRequest(request, authorization);
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
            HttpServletRequest request,
            @Parameter(description = "Document ID") @PathVariable String documentId,
            @Parameter(description = "Authorization header (optional, will try cookies first)") @RequestHeader(value = "Authorization", required = false) String authorization) {
        
        try {
            UUID documentUuid = UUID.fromString(documentId);
            
            // Extract user ID from cookies or authorization header
            String userId = authUtils.extractUserIdFromRequest(request, authorization);
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
            HttpServletRequest request,
            @Parameter(description = "Document ID") @PathVariable String documentId,
            @Parameter(description = "Authorization header (optional, will try cookies first)") @RequestHeader(value = "Authorization", required = false) String authorization) {
        
        try {
            UUID documentUuid = UUID.fromString(documentId);
            
            // Extract user ID from cookies or authorization header
            String userId = authUtils.extractUserIdFromRequest(request, authorization);
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
            HttpServletRequest request,
            @Parameter(description = "Document ID") @PathVariable String documentId,
            @Parameter(description = "Authorization header (optional, will try cookies first)") @RequestHeader(value = "Authorization", required = false) String authorization) {
        
        try {
            UUID documentUuid = UUID.fromString(documentId);
            
            // Extract user ID from cookies or authorization header
            String userId = authUtils.extractUserIdFromRequest(request, authorization);
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
            HttpServletRequest request,
            @Parameter(description = "Document ID") @PathVariable String documentId,
            @Parameter(description = "Authorization header (optional, will try cookies first)") @RequestHeader(value = "Authorization", required = false) String authorization) {
        
        try {
            UUID documentUuid = UUID.fromString(documentId);
            
            // Extract user ID from cookies or authorization header
            String userId = authUtils.extractUserIdFromRequest(request, authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }
            
            String analysisId = documentService.reanalyzeDocument(documentUuid, userId, null); // No authToken needed for reanalysis
            
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

    @Operation(summary = "Export document analysis as PDF", description = "Exports the analysis results for a document as a PDF report")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "PDF report generated successfully",
                content = @Content(mediaType = "application/pdf")),
        @ApiResponse(responseCode = "404", description = "Document or analysis not found",
                content = @Content(mediaType = "application/json")),
        @ApiResponse(responseCode = "401", description = "Authentication required",
                content = @Content(mediaType = "application/json"))
    })
    @GetMapping("/documents/{documentId}/analysis/export")
    public ResponseEntity<?> exportDocumentAnalysisPdf(
            HttpServletRequest request,
            @Parameter(description = "Document ID") @PathVariable String documentId,
            @Parameter(description = "Authorization header (optional, will try cookies first)") @RequestHeader(value = "Authorization", required = false) String authorization) {
        
        try {
            UUID documentUuid = UUID.fromString(documentId);
            
            // Extract user ID from cookies or authorization header
            String userId = authUtils.extractUserIdFromRequest(request, authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }
            
            byte[] pdfBytes = documentService.exportDocumentAnalysisPdf(documentUuid, userId, null); // No authToken needed for export
            
            if (pdfBytes == null) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(Map.of("error", "Analysis not found for this document"));
            }
            
            return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_PDF_VALUE)
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=analysis_report_" + documentId + ".pdf")
                .header(HttpHeaders.CONTENT_LENGTH, String.valueOf(pdfBytes.length))
                .body(pdfBytes);
                
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", "Invalid document ID format"));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to export analysis PDF"));
        }
    }
} 