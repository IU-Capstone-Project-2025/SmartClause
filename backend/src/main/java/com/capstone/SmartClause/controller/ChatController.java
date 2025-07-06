package com.capstone.SmartClause.controller;

import com.capstone.SmartClause.model.dto.ChatDto;
import com.capstone.SmartClause.service.ChatService;
import com.capstone.SmartClause.util.AuthUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;

import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*", methods = {RequestMethod.GET, RequestMethod.POST, RequestMethod.PUT, RequestMethod.DELETE}, maxAge = 3600)
@Tag(name = "Chat API Gateway", description = "API gateway for chat microservice functionality")
public class ChatController {

    @Autowired
    private ChatService chatService;
    
    @Autowired
    private AuthUtils authUtils;



    @Operation(summary = "Get chat messages for a space", description = "Retrieves chat messages for a specific space with pagination")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Messages retrieved successfully",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = ChatDto.GetMessagesResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid request parameters",
                content = @Content(mediaType = "application/json")),
        @ApiResponse(responseCode = "401", description = "Authentication required",
                content = @Content(mediaType = "application/json"))
    })
    @GetMapping("/spaces/{spaceId}/messages")
    public ResponseEntity<?> getMessages(
            @Parameter(description = "Authorization header") @RequestHeader(value = "Authorization", required = false) String authorization,
            @Parameter(description = "Space ID") @PathVariable String spaceId,
            @Parameter(description = "Maximum number of messages to retrieve") @RequestParam(defaultValue = "50") int limit,
            @Parameter(description = "Number of messages to skip") @RequestParam(defaultValue = "0") int offset) {
        
        try {
            // Extract user ID from authorization header (for consistency with other endpoints)
            String userId = authUtils.extractUserIdFromHeader(authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }

            ChatDto.GetMessagesResponse response = chatService.getMessages(spaceId, limit, offset, authorization);
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to retrieve messages"));
        }
    }

    @Operation(summary = "Send a message to space chat", description = "Sends a message to the chat in a specific space")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Message sent successfully",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = ChatDto.SendMessageResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid message data",
                content = @Content(mediaType = "application/json")),
        @ApiResponse(responseCode = "401", description = "Authentication required",
                content = @Content(mediaType = "application/json"))
    })
    @PostMapping("/spaces/{spaceId}/messages")
    public ResponseEntity<?> sendMessage(
            @Parameter(description = "Authorization header") @RequestHeader(value = "Authorization", required = false) String authorization,
            @Parameter(description = "Space ID") @PathVariable String spaceId,
            @RequestBody ChatDto.SendMessageRequest request) {
        
        try {
            // Extract user ID from authorization header
            String userId = authUtils.extractUserIdFromHeader(authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }

            // Validate request
            if (request.getContent() == null || request.getContent().trim().isEmpty()) {
                return ResponseEntity.badRequest()
                    .body(Map.of("error", "Message content cannot be empty"));
            }

            ChatDto.SendMessageResponse response = chatService.sendMessage(spaceId, request, authorization);
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to send message"));
        }
    }

    @Operation(summary = "Get chat session information", description = "Retrieves chat session information for a specific space")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Chat session information retrieved successfully",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = ChatDto.ChatSessionResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid space ID",
                content = @Content(mediaType = "application/json")),
        @ApiResponse(responseCode = "401", description = "Authentication required",
                content = @Content(mediaType = "application/json"))
    })
    @GetMapping("/spaces/{spaceId}/session")
    public ResponseEntity<?> getChatSession(
            @Parameter(description = "Authorization header") @RequestHeader(value = "Authorization", required = false) String authorization,
            @Parameter(description = "Space ID") @PathVariable String spaceId) {
        
        try {
            // Extract user ID from authorization header
            String userId = authUtils.extractUserIdFromHeader(authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }

            ChatDto.ChatSessionResponse response = chatService.getChatSession(spaceId, authorization);
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to retrieve chat session"));
        }
    }

    @Operation(summary = "Update memory length for chat session", description = "Updates the memory length configuration for a chat session")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Memory length updated successfully",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = ChatDto.ChatSessionResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid request data",
                content = @Content(mediaType = "application/json")),
        @ApiResponse(responseCode = "401", description = "Authentication required",
                content = @Content(mediaType = "application/json"))
    })
    @PutMapping("/spaces/{spaceId}/session/memory")
    public ResponseEntity<?> updateMemoryLength(
            @Parameter(description = "Authorization header") @RequestHeader(value = "Authorization", required = false) String authorization,
            @Parameter(description = "Space ID") @PathVariable String spaceId,
            @RequestBody ChatDto.ChatMemoryConfigRequest request) {
        
        try {
            // Extract user ID from authorization header
            String userId = authUtils.extractUserIdFromHeader(authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }

            // Validate memory length
            if (request.getMemoryLength() < 1 || request.getMemoryLength() > 50) {
                return ResponseEntity.badRequest()
                    .body(Map.of("error", "Memory length must be between 1 and 50"));
            }

            ChatDto.ChatSessionResponse response = chatService.updateMemoryLength(spaceId, request, authorization);
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to update memory length"));
        }
    }
} 