package com.capstone.SmartClause.service;

import com.capstone.SmartClause.model.User;
import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

@Service
public class JwtService {
    
    private static final Logger logger = LoggerFactory.getLogger(JwtService.class);
    
    @Value("${app.jwt.secret:SmartClauseSecretKeyThatIsAtLeast32CharactersLongForHS256}")
    private String jwtSecret;
    
    @Value("${app.jwt.expiration:86400}") // 24 hours in seconds
    private long jwtExpirationInSeconds;
    
    @Value("${app.jwt.refresh-expiration:604800}") // 7 days in seconds  
    private long refreshExpirationInSeconds;
    
    /**
     * Extract username from JWT token
     */
    public String extractUsername(String token) {
        return extractClaim(token, Claims::getSubject);
    }
    
    /**
     * Extract user ID from JWT token
     */
    public String extractUserId(String token) {
        return extractClaim(token, claims -> claims.get("userId", String.class));
    }
    
    /**
     * Extract user role from JWT token
     */
    public String extractUserRole(String token) {
        return extractClaim(token, claims -> claims.get("role", String.class));
    }
    
    /**
     * Extract expiration date from JWT token
     */
    public Date extractExpiration(String token) {
        return extractClaim(token, Claims::getExpiration);
    }
    
    /**
     * Extract a specific claim from JWT token
     */
    public <T> T extractClaim(String token, Function<Claims, T> claimsResolver) {
        final Claims claims = extractAllClaims(token);
        return claimsResolver.apply(claims);
    }
    
    /**
     * Generate JWT token for user
     */
    public String generateToken(User user) {
        Map<String, Object> extraClaims = new HashMap<>();
        extraClaims.put("userId", user.getId().toString());
        extraClaims.put("email", user.getEmail());
        extraClaims.put("role", user.getRole().name());
        extraClaims.put("isEmailVerified", user.getIsEmailVerified());
        
        return generateToken(extraClaims, user);
    }
    
    /**
     * Generate system token for service account operations.
     * Used for internal microservice communication when handling public requests.
     */
    public String generateSystemToken() {
        Map<String, Object> extraClaims = new HashMap<>();
        extraClaims.put("userId", "system");
        extraClaims.put("email", "system@smartclause.internal");
        extraClaims.put("role", "SYSTEM");
        extraClaims.put("isEmailVerified", true);
        extraClaims.put("serviceAccount", true);
        
        // Create a minimal UserDetails implementation for system account
        UserDetails systemUser = new org.springframework.security.core.userdetails.User(
            "system", 
            "", // No password needed for service account
            List.of(new org.springframework.security.core.authority.SimpleGrantedAuthority("ROLE_SYSTEM"))
        );
        
        return generateToken(extraClaims, systemUser);
    }
    
    /**
     * Generate JWT token with extra claims
     */
    public String generateToken(Map<String, Object> extraClaims, UserDetails userDetails) {
        return buildToken(extraClaims, userDetails, jwtExpirationInSeconds);
    }
    
    /**
     * Generate refresh token
     */
    public String generateRefreshToken(UserDetails userDetails) {
        return buildToken(new HashMap<>(), userDetails, refreshExpirationInSeconds);
    }
    
    /**
     * Build JWT token with specified expiration
     */
    private String buildToken(
            Map<String, Object> extraClaims,
            UserDetails userDetails,
            long expirationInSeconds
    ) {
        Instant now = Instant.now();
        Instant expiration = now.plus(expirationInSeconds, ChronoUnit.SECONDS);
        
        return Jwts.builder()
                .setClaims(extraClaims)
                .setSubject(userDetails.getUsername())
                .setIssuedAt(Date.from(now))
                .setExpiration(Date.from(expiration))
                .signWith(getSignInKey(), SignatureAlgorithm.HS256)
                .compact();
    }
    
    /**
     * Validate JWT token against UserDetails
     */
    public boolean isTokenValid(String token, UserDetails userDetails) {
        try {
            final String username = extractUsername(token);
            return (username.equals(userDetails.getUsername())) && !isTokenExpired(token);
        } catch (Exception e) {
            logger.warn("Token validation failed: {}", e.getMessage());
            return false;
        }
    }
    
    /**
     * Check if JWT token is expired
     */
    public boolean isTokenExpired(String token) {
        try {
            return extractExpiration(token).before(new Date());
        } catch (Exception e) {
            logger.warn("Error checking token expiration: {}", e.getMessage());
            return true;
        }
    }
    
    /**
     * Validate JWT token format and signature
     */
    public boolean isTokenValidFormat(String token) {
        try {
            extractAllClaims(token);
            return true;
        } catch (MalformedJwtException e) {
            logger.warn("Invalid JWT token format: {}", e.getMessage());
        } catch (ExpiredJwtException e) {
            logger.warn("JWT token is expired: {}", e.getMessage());
        } catch (UnsupportedJwtException e) {
            logger.warn("JWT token is unsupported: {}", e.getMessage());
        } catch (IllegalArgumentException e) {
            logger.warn("JWT claims string is empty: {}", e.getMessage());
        } catch (Exception e) {
            logger.warn("JWT token validation error: {}", e.getMessage());
        }
        return false;
    }
    
    /**
     * Extract all claims from JWT token
     */
    private Claims extractAllClaims(String token) {
        return Jwts.parser()
                .verifyWith(getSignInKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }
    
    /**
     * Get signing key for JWT tokens
     */
    private SecretKey getSignInKey() {
        byte[] keyBytes = jwtSecret.getBytes();
        return Keys.hmacShaKeyFor(keyBytes);
    }
    
    /**
     * Get JWT expiration time in seconds
     */
    public long getExpirationTime() {
        return jwtExpirationInSeconds;
    }
    
    /**
     * Get refresh token expiration time in seconds
     */
    public long getRefreshExpirationTime() {
        return refreshExpirationInSeconds;
    }
    
    /**
     * Extract token from Authorization header
     */
    public String extractTokenFromHeader(String authorizationHeader) {
        if (authorizationHeader != null && authorizationHeader.startsWith("Bearer ")) {
            return authorizationHeader.substring(7);
        }
        return null;
    }
} 