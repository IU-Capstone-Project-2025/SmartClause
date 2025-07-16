package com.capstone.SmartClause.controller;

import com.capstone.SmartClause.service.RateLimitService;
import com.capstone.SmartClause.util.AuthUtils;
import com.capstone.SmartClause.util.UserIdentificationUtils;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/rate-limit")
@Tag(name = "Rate Limit Management", description = "Endpoints for monitoring and managing rate limits")
public class RateLimitController {
    
    private static final Logger logger = LoggerFactory.getLogger(RateLimitController.class);
    
    @Autowired
    private RateLimitService rateLimitService;
    
    @Autowired
    private UserIdentificationUtils userIdentificationUtils;
    
    @Autowired
    private AuthUtils authUtils;
    
    @Operation(summary = "Get current rate limit status", 
              description = "Get the current rate limit status for the requesting user")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Rate limit status retrieved successfully"),
        @ApiResponse(responseCode = "500", description = "Internal server error")
    })
    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> getRateLimitStatus(
            HttpServletRequest request,
            @Parameter(description = "Authorization header (optional)") 
            @RequestHeader(value = "Authorization", required = false) String authorization) {
        
        try {
            // Extract user ID from authentication
            String userId = authUtils.extractUserIdFromRequest(request, authorization);
            
            // Generate unique identifier for rate limiting
            String userIdentifier = userIdentificationUtils.generateUserIdentifier(request, userId);
            boolean isAuthenticated = userIdentificationUtils.isAuthenticatedUser(userIdentifier);
            
            // Get current usage and remaining requests
            RateLimitService.RateLimitResult current = rateLimitService.getCurrentUsage(userIdentifier, isAuthenticated);
            RateLimitService.RateLimitRemaining remaining = rateLimitService.getRemainingRequests(userIdentifier, isAuthenticated);
            
            Map<String, Object> response = new HashMap<>();
            response.put("userType", isAuthenticated ? "authenticated" : "anonymous");
            response.put("userIdentifier", userIdentifier.substring(0, Math.min(16, userIdentifier.length())) + "...");
            
            Map<String, Object> usage = new HashMap<>();
            usage.put("minute", current.getMinuteCount());
            usage.put("hour", current.getHourCount());
            usage.put("day", current.getDayCount());
            response.put("usage", usage);
            
            Map<String, Object> remainingMap = new HashMap<>();
            remainingMap.put("minute", remaining.getMinuteRemaining());
            remainingMap.put("hour", remaining.getHourRemaining());
            remainingMap.put("day", remaining.getDayRemaining());
            response.put("remaining", remainingMap);
            
            logger.debug("Rate limit status requested for user: {}", userIdentifier);
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error getting rate limit status", e);
            return ResponseEntity.internalServerError()
                .body(Map.of("error", "Failed to get rate limit status: " + e.getMessage()));
        }
    }
    
    @Operation(summary = "Get rate limit cache statistics", 
              description = "Get statistics about the rate limiting cache (for monitoring)")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Cache statistics retrieved successfully"),
        @ApiResponse(responseCode = "401", description = "Authentication required"),
        @ApiResponse(responseCode = "403", description = "Insufficient permissions")
    })
    @SecurityRequirement(name = "bearer-key")
    @GetMapping("/cache-stats")
    public ResponseEntity<Map<String, Object>> getCacheStats(
            HttpServletRequest request,
            @Parameter(description = "Authorization header") 
            @RequestHeader(value = "Authorization", required = false) String authorization) {
        
        try {
            // Only allow authenticated users to view cache stats
            String userId = authUtils.extractUserIdFromRequest(request, authorization);
            if (userId == null || "system".equals(userId)) {
                return ResponseEntity.status(401)
                    .body(Map.of("error", "Authentication required"));
            }
            
            String cacheStats = rateLimitService.getCacheStats();
            
            Map<String, Object> response = new HashMap<>();
            response.put("cacheStats", cacheStats);
            response.put("timestamp", System.currentTimeMillis());
            
            logger.debug("Cache statistics requested by user: {}", userId);
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error getting cache statistics", e);
            return ResponseEntity.internalServerError()
                .body(Map.of("error", "Failed to get cache statistics: " + e.getMessage()));
        }
    }
    
    @Operation(summary = "Clear rate limit for current user", 
              description = "Clear the rate limit data for the current user (useful for testing)")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Rate limit cleared successfully"),
        @ApiResponse(responseCode = "401", description = "Authentication required")
    })
    @SecurityRequirement(name = "bearer-key")
    @DeleteMapping("/clear")
    public ResponseEntity<Map<String, Object>> clearUserRateLimit(
            HttpServletRequest request,
            @Parameter(description = "Authorization header") 
            @RequestHeader(value = "Authorization", required = false) String authorization) {
        
        try {
            // Extract user ID from authentication
            String userId = authUtils.extractUserIdFromRequest(request, authorization);
            
            // Generate unique identifier for rate limiting
            String userIdentifier = userIdentificationUtils.generateUserIdentifier(request, userId);
            
            // Clear rate limit for this user
            rateLimitService.clearUserRateLimit(userIdentifier);
            
            Map<String, Object> response = new HashMap<>();
            response.put("message", "Rate limit cleared successfully");
            response.put("userIdentifier", userIdentifier.substring(0, Math.min(16, userIdentifier.length())) + "...");
            
            logger.info("Rate limit cleared for user: {}", userIdentifier);
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error clearing rate limit", e);
            return ResponseEntity.internalServerError()
                .body(Map.of("error", "Failed to clear rate limit: " + e.getMessage()));
        }
    }
} 