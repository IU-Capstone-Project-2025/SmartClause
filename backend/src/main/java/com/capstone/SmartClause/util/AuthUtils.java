package com.capstone.SmartClause.util;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class AuthUtils {
    
    private static final Logger logger = LoggerFactory.getLogger(AuthUtils.class);
    
    /**
     * Extracts user ID from Authorization header.
     * 
     * For now, this is a placeholder implementation that returns a default user.
     * In the future, this will:
     * 1. Parse JWT token from "Bearer <token>" format
     * 2. Validate token signature and expiration
     * 3. Extract user ID from token claims
     * 4. Handle token refresh if needed
     * 
     * @param authorizationHeader The Authorization header value
     * @return User ID string, or null if not authenticated
     */
    public String extractUserIdFromHeader(String authorizationHeader) {
        try {
            // TODO: Replace with actual JWT parsing when authentication is implemented
            if (authorizationHeader == null || authorizationHeader.trim().isEmpty()) {
                logger.debug("No authorization header provided");
                return getDefaultUserId();
            }
            
            // For now, treat any authorization header as valid and return default user
            // Future implementation will parse JWT token here
            if (authorizationHeader.startsWith("Bearer ")) {
                String token = authorizationHeader.substring(7);
                logger.debug("Received Bearer token: {}", token.substring(0, Math.min(token.length(), 10)) + "...");
                
                // TODO: Parse JWT token and extract user ID
                // Example future implementation:
                // Claims claims = Jwts.parser().setSigningKey(jwtSecret).parseClaimsJws(token).getBody();
                // return claims.getSubject(); // user ID
                
                return getDefaultUserId();
            }
            
            logger.debug("Authorization header format not recognized");
            return getDefaultUserId();
            
        } catch (Exception e) {
            logger.error("Failed to extract user ID from authorization header", e);
            return null; // Return null for invalid tokens
        }
    }
    
    /**
     * Returns a default user ID for development/testing purposes.
     * Remove this method when real authentication is implemented.
     * 
     * @return Default user ID
     */
    private String getDefaultUserId() {
        // For development, return a consistent default user ID
        // This allows testing user-specific functionality
        return "default-user-123";
    }
    
    /**
     * Checks if a user is authenticated based on the authorization header.
     * 
     * @param authorizationHeader The Authorization header value
     * @return true if user is authenticated, false otherwise
     */
    public boolean isAuthenticated(String authorizationHeader) {
        return extractUserIdFromHeader(authorizationHeader) != null;
    }
    
    /**
     * Validates if the provided user ID matches the authenticated user.
     * Useful for ensuring users can only access their own resources.
     * 
     * @param authorizationHeader The Authorization header value
     * @param resourceUserId The user ID associated with the resource
     * @return true if the authenticated user owns the resource
     */
    public boolean isOwner(String authorizationHeader, String resourceUserId) {
        String authenticatedUserId = extractUserIdFromHeader(authorizationHeader);
        return authenticatedUserId != null && authenticatedUserId.equals(resourceUserId);
    }
} 