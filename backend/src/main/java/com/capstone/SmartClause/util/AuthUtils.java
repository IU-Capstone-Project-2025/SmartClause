package com.capstone.SmartClause.util;

import com.capstone.SmartClause.service.JwtService;
import com.capstone.SmartClause.service.UserService;
import com.capstone.SmartClause.model.User;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.Optional;
import java.util.UUID;

@Component
public class AuthUtils {
    
    private static final Logger logger = LoggerFactory.getLogger(AuthUtils.class);
    
    @Autowired
    private JwtService jwtService;
    
    @Autowired
    private UserService userService;
    
    /**
     * Extracts user ID from Authorization header by parsing and validating JWT token.
     * 
     * @param authorizationHeader The Authorization header value in format "Bearer <token>"
     * @return User ID string, or null if not authenticated
     */
    public String extractUserIdFromHeader(String authorizationHeader) {
        try {
            if (authorizationHeader == null || authorizationHeader.trim().isEmpty()) {
                logger.debug("No authorization header provided");
                return null;
            }
            
            if (!authorizationHeader.startsWith("Bearer ")) {
                logger.debug("Authorization header is not in Bearer format");
                return null;
            }
            
            String token = authorizationHeader.substring(7);
            
            // Validate token format first
            if (!jwtService.isTokenValidFormat(token)) {
                logger.debug("Invalid JWT token format");
                return null;
            }
            
            // Extract user ID from token
            String userId = jwtService.extractUserId(token);
            if (userId == null) {
                logger.debug("No user ID found in token");
                return null;
            }
            
            // Verify user exists and is active
            Optional<User> userOpt = userService.findById(UUID.fromString(userId));
            if (userOpt.isEmpty()) {
                logger.debug("User not found for ID: {}", userId);
                return null;
            }
            
            User user = userOpt.get();
            if (!user.getIsActive()) {
                logger.debug("User account is deactivated: {}", userId);
                return null;
            }
            
            // Additional token validation against user
            if (!jwtService.isTokenValid(token, user)) {
                logger.debug("Token validation failed for user: {}", userId);
                return null;
            }
            
            logger.debug("Successfully authenticated user: {}", userId);
            return userId;
            
        } catch (Exception e) {
            logger.error("Failed to extract user ID from authorization header: {}", e.getMessage());
            return null;
        }
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