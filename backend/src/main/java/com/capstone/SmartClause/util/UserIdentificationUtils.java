package com.capstone.SmartClause.util;

import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.stream.Stream;

@Component
public class UserIdentificationUtils {
    
    private static final Logger logger = LoggerFactory.getLogger(UserIdentificationUtils.class);
    
    /**
     * Generate a unique identifier for rate limiting purposes.
     * For authenticated users, uses the user ID.
     * For anonymous users, creates a fingerprint based on IP, User-Agent, and other headers.
     * 
     * @param request HTTP request
     * @param userId Optional user ID from authentication (null for anonymous users)
     * @return Unique identifier string
     */
    public String generateUserIdentifier(HttpServletRequest request, String userId) {
        if (userId != null && !userId.trim().isEmpty() && !"system".equals(userId)) {
            // Authenticated user - use user ID
            logger.debug("Generated authenticated user identifier: {}", userId);
            return "auth:" + userId;
        }
        
        // Anonymous user - create fingerprint
        String fingerprint = createAnonymousFingerprint(request);
        logger.debug("Generated anonymous user identifier: {}", fingerprint);
        return "anon:" + fingerprint;
    }
    
    /**
     * Creates a fingerprint for anonymous users based on request characteristics.
     * This provides reasonable uniqueness while preserving privacy.
     */
    private String createAnonymousFingerprint(HttpServletRequest request) {
        String clientIp = getClientIpAddress(request);
        String userAgent = request.getHeader("User-Agent");
        String acceptLanguage = request.getHeader("Accept-Language");
        String acceptEncoding = request.getHeader("Accept-Encoding");
        
        // Create a concatenated string of identifying characteristics
        String rawFingerprint = Stream.of(
            clientIp,
            userAgent != null ? userAgent : "unknown",
            acceptLanguage != null ? acceptLanguage : "",
            acceptEncoding != null ? acceptEncoding : ""
        ).reduce("", (a, b) -> a + "|" + b);
        
        // Hash the fingerprint for privacy and consistent length
        return hashString(rawFingerprint);
    }
    
    /**
     * Extract the real client IP address, handling common proxy headers.
     */
    private String getClientIpAddress(HttpServletRequest request) {
        String xForwardedFor = request.getHeader("X-Forwarded-For");
        if (xForwardedFor != null && !xForwardedFor.isEmpty() && !"unknown".equalsIgnoreCase(xForwardedFor)) {
            // X-Forwarded-For can contain multiple IPs, get the first one
            return xForwardedFor.split(",")[0].trim();
        }
        
        String xRealIp = request.getHeader("X-Real-IP");
        if (xRealIp != null && !xRealIp.isEmpty() && !"unknown".equalsIgnoreCase(xRealIp)) {
            return xRealIp;
        }
        
        String xForwarded = request.getHeader("X-Forwarded");
        if (xForwarded != null && !xForwarded.isEmpty() && !"unknown".equalsIgnoreCase(xForwarded)) {
            return xForwarded;
        }
        
        String forwardedFor = request.getHeader("Forwarded-For");
        if (forwardedFor != null && !forwardedFor.isEmpty() && !"unknown".equalsIgnoreCase(forwardedFor)) {
            return forwardedFor;
        }
        
        String forwarded = request.getHeader("Forwarded");
        if (forwarded != null && !forwarded.isEmpty() && !"unknown".equalsIgnoreCase(forwarded)) {
            return forwarded;
        }
        
        // Fall back to remote address
        return request.getRemoteAddr();
    }
    
    /**
     * Hash a string using SHA-256 for consistent fingerprinting.
     */
    private String hashString(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(input.getBytes());
            StringBuilder hexString = new StringBuilder();
            
            for (byte b : hash) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) {
                    hexString.append('0');
                }
                hexString.append(hex);
            }
            
            // Return first 16 characters for shorter identifiers
            return hexString.substring(0, 16);
            
        } catch (NoSuchAlgorithmException e) {
            logger.error("SHA-256 algorithm not available", e);
            // Fallback to simple hash code
            return String.valueOf(Math.abs(input.hashCode()));
        }
    }
    
    /**
     * Determine if a user identifier represents an authenticated user.
     */
    public boolean isAuthenticatedUser(String userIdentifier) {
        return userIdentifier != null && userIdentifier.startsWith("auth:");
    }
    
    /**
     * Determine if a user identifier represents an anonymous user.
     */
    public boolean isAnonymousUser(String userIdentifier) {
        return userIdentifier != null && userIdentifier.startsWith("anon:");
    }
} 