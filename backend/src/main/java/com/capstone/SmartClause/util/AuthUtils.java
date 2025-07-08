package com.capstone.SmartClause.util;

import com.capstone.SmartClause.service.JwtService;
import com.capstone.SmartClause.service.UserService;
import com.capstone.SmartClause.model.User;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import java.util.Optional;
import java.util.UUID;

@Component
public class AuthUtils {
    
    private static final Logger logger = LoggerFactory.getLogger(AuthUtils.class);
    private static final String JWT_COOKIE_NAME = "smartclause_token";
    
    @Autowired
    private JwtService jwtService;
    
    @Autowired
    private UserService userService;
    
    /**
     * Extracts JWT token from cookie.
     * 
     * @param request The HTTP request containing cookies
     * @return JWT token string, or null if not found
     */
    public String extractTokenFromCookie(HttpServletRequest request) {
        if (request == null) {
            return null;
        }
        
        Cookie[] cookies = request.getCookies();
        if (cookies == null) {
            return null;
        }
        
        for (Cookie cookie : cookies) {
            if (JWT_COOKIE_NAME.equals(cookie.getName())) {
                String token = cookie.getValue();
                if (token != null && !token.trim().isEmpty()) {
                    logger.debug("Found JWT token in cookie");
                    return token;
                }
            }
        }
        
        return null;
    }
    
    /**
     * Extracts JWT token from Authorization header.
     * 
     * @param authorizationHeader The Authorization header value in format "Bearer <token>"
     * @return JWT token string, or null if not found
     */
    public String extractTokenFromHeader(String authorizationHeader) {
        if (authorizationHeader == null || authorizationHeader.trim().isEmpty()) {
            return null;
        }
        
        if (!authorizationHeader.startsWith("Bearer ")) {
            return null;
        }
        
        return authorizationHeader.substring(7);
    }
    
    /**
     * Validates JWT token and extracts user ID.
     * 
     * @param token The JWT token to validate
     * @return User ID string, or null if token is invalid
     */
    public String validateTokenAndExtractUserId(String token) {
        try {
            if (token == null || token.trim().isEmpty()) {
                return null;
            }
            
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
            logger.error("Failed to validate token and extract user ID: {}", e.getMessage());
            return null;
        }
    }
    
    /**
     * Extracts user ID from request (trying both cookies and Authorization header).
     * First tries to get token from cookie, then falls back to Authorization header for backward compatibility.
     * 
     * @param request The HTTP request (can be null for backward compatibility)
     * @param authorizationHeader The Authorization header value (can be null)
     * @return User ID string, or null if not authenticated
     */
    public String extractUserIdFromRequest(HttpServletRequest request, String authorizationHeader) {
        try {
            String token = null;
            
            // First try to get token from cookie
            if (request != null) {
                token = extractTokenFromCookie(request);
                if (token != null) {
                    logger.debug("Using JWT token from cookie");
                }
            }
            
            // If no token from cookie, try Authorization header
            if (token == null) {
                token = extractTokenFromHeader(authorizationHeader);
                if (token != null) {
                    logger.debug("Using JWT token from Authorization header");
                }
            }
            
            // Validate token and extract user ID
            return validateTokenAndExtractUserId(token);
            
        } catch (Exception e) {
            logger.error("Failed to extract user ID from request: {}", e.getMessage());
            return null;
        }
    }
    
    /**
     * Extracts user ID from Authorization header by parsing and validating JWT token.
     * This method is kept for backward compatibility.
     * 
     * @param authorizationHeader The Authorization header value in format "Bearer <token>"
     * @return User ID string, or null if not authenticated
     */
    public String extractUserIdFromHeader(String authorizationHeader) {
        return extractUserIdFromRequest(null, authorizationHeader);
    }
    
    /**
     * Checks if a user is authenticated based on the request (cookies or authorization header).
     * 
     * @param request The HTTP request
     * @param authorizationHeader The Authorization header value
     * @return true if user is authenticated, false otherwise
     */
    public boolean isAuthenticated(HttpServletRequest request, String authorizationHeader) {
        return extractUserIdFromRequest(request, authorizationHeader) != null;
    }
    
    /**
     * Checks if a user is authenticated based on the authorization header.
     * This method is kept for backward compatibility.
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
     * @param request The HTTP request
     * @param authorizationHeader The Authorization header value
     * @param resourceUserId The user ID associated with the resource
     * @return true if the authenticated user owns the resource
     */
    public boolean isOwner(HttpServletRequest request, String authorizationHeader, String resourceUserId) {
        String authenticatedUserId = extractUserIdFromRequest(request, authorizationHeader);
        return authenticatedUserId != null && authenticatedUserId.equals(resourceUserId);
    }
    
    /**
     * Validates if the provided user ID matches the authenticated user.
     * This method is kept for backward compatibility.
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