package com.capstone.SmartClause.controller;

import com.capstone.SmartClause.model.dto.SpaceDto;
import com.capstone.SmartClause.service.SpaceService;
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

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@RestController
@RequestMapping("/api/spaces")
@CrossOrigin(origins = "*", methods = {RequestMethod.GET, RequestMethod.POST, RequestMethod.PUT, RequestMethod.DELETE}, maxAge = 3600)
@Tag(name = "Spaces API", description = "API for managing document spaces")
public class SpaceController {

    @Autowired
    private SpaceService spaceService;
    
    @Autowired
    private AuthUtils authUtils;

    @Operation(summary = "Get all user spaces", description = "Retrieves all spaces for the authenticated user")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Spaces retrieved successfully",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = SpaceDto.SpaceListResponse.class)))
    })
    @GetMapping
    public ResponseEntity<?> getAllSpaces(
            @Parameter(description = "Authorization header") @RequestHeader(value = "Authorization", required = false) String authorization) {
        
        try {
            // Extract user ID from authorization header
            String userId = authUtils.extractUserIdFromHeader(authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }
            
            // Get user-specific spaces
            List<SpaceDto.SpaceListItem> spaces = spaceService.getSpacesByUser(userId);
            
            SpaceDto.SpaceListResponse response = new SpaceDto.SpaceListResponse();
            response.setSpaces(spaces);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to retrieve spaces"));
        }
    }

    @Operation(summary = "Create new space", description = "Creates a new document space")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "201", description = "Space created successfully",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = SpaceDto.SpaceResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid request data",
                content = @Content(mediaType = "application/json"))
    })
    @PostMapping
    public ResponseEntity<?> createSpace(
            @Parameter(description = "Authorization header") @RequestHeader(value = "Authorization", required = false) String authorization,
            @RequestBody SpaceDto.CreateSpaceRequest request) {
        
        try {
            if (request.getName() == null || request.getName().trim().isEmpty()) {
                return ResponseEntity.badRequest()
                    .body(Map.of("error", "Space name is required"));
            }

            // Extract user ID from authorization header
            String userId = authUtils.extractUserIdFromHeader(authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }
            
            SpaceDto.SpaceResponse space = spaceService.createSpace(request, userId);
            
            return ResponseEntity.status(HttpStatus.CREATED)
                .body(Map.of("space", space));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to create space"));
        }
    }

    @Operation(summary = "Get space details", description = "Retrieves detailed information about a specific space")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Space details retrieved successfully",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = SpaceDto.SpaceDetailResponse.class))),
        @ApiResponse(responseCode = "404", description = "Space not found",
                content = @Content(mediaType = "application/json"))
    })
    @GetMapping("/{spaceId}")
    public ResponseEntity<?> getSpaceDetails(
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
            
            Optional<SpaceDto.SpaceDetailResponse> spaceOpt = spaceService.getSpaceByIdAndUser(spaceUuid, userId);
            
            if (spaceOpt.isEmpty()) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(Map.of("error", "Space not found"));
            }
            
            return ResponseEntity.ok(Map.of("space", spaceOpt.get()));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", "Invalid space ID format"));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to retrieve space details"));
        }
    }

    @Operation(summary = "Update space details", description = "Updates name and/or description of a space")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Space updated successfully",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = SpaceDto.SpaceResponse.class))),
        @ApiResponse(responseCode = "404", description = "Space not found",
                content = @Content(mediaType = "application/json"))
    })
    @PutMapping("/{spaceId}")
    public ResponseEntity<?> updateSpace(
            @Parameter(description = "Authorization header") @RequestHeader(value = "Authorization", required = false) String authorization,
            @Parameter(description = "Space ID") @PathVariable String spaceId,
            @RequestBody SpaceDto.UpdateSpaceRequest request) {
        
        try {
            UUID spaceUuid = UUID.fromString(spaceId);
            
            // Extract user ID from authorization header
            String userId = authUtils.extractUserIdFromHeader(authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }
            
            Optional<SpaceDto.SpaceResponse> updatedSpaceOpt = spaceService.updateSpace(spaceUuid, request, userId);
            
            if (updatedSpaceOpt.isEmpty()) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(Map.of("error", "Space not found"));
            }
            
            return ResponseEntity.ok(Map.of("space", updatedSpaceOpt.get()));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", "Invalid space ID format"));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to update space"));
        }
    }

    @Operation(summary = "Delete space", description = "Deletes a space and all its documents")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "204", description = "Space deleted successfully"),
        @ApiResponse(responseCode = "404", description = "Space not found",
                content = @Content(mediaType = "application/json"))
    })
    @DeleteMapping("/{spaceId}")
    public ResponseEntity<?> deleteSpace(
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
            
            boolean deleted = spaceService.deleteSpace(spaceUuid, userId);
            
            if (!deleted) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(Map.of("error", "Space not found"));
            }
            
            return ResponseEntity.noContent().build();
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                .body(Map.of("error", "Invalid space ID format"));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to delete space"));
        }
    }
} 