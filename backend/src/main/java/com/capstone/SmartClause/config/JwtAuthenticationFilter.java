package com.capstone.SmartClause.config;

import com.capstone.SmartClause.service.JwtService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.lang.NonNull;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private static final Logger logger = LoggerFactory.getLogger(JwtAuthenticationFilter.class);
    private static final String JWT_COOKIE_NAME = "smartclause_token";

    private final JwtService jwtService;
    private final UserDetailsService userDetailsService;

    public JwtAuthenticationFilter(JwtService jwtService, UserDetailsService userDetailsService) {
        this.jwtService = jwtService;
        this.userDetailsService = userDetailsService;
    }

    @Override
    protected void doFilterInternal(
            @NonNull HttpServletRequest request,
            @NonNull HttpServletResponse response,
            @NonNull FilterChain filterChain
    ) throws ServletException, IOException {

        String path = request.getServletPath();
        logger.debug("Processing request path: {}", path);

        // Skip authentication for public endpoints
        if (isPublicEndpoint(path)) {
            logger.debug("Skipping JWT authentication for public endpoint: {}", path);
            filterChain.doFilter(request, response);
            return;
        }

        try {
            // Extract JWT token from cookie or Authorization header
            String jwt = extractJwtToken(request);

            if (jwt != null && SecurityContextHolder.getContext().getAuthentication() == null) {
                logger.debug("Processing JWT token for authentication");
                
                // Validate token format first
                if (!jwtService.isTokenValidFormat(jwt)) {
                    logger.debug("Invalid JWT token format");
                    filterChain.doFilter(request, response);
                    return;
                }

                // Extract username from token
                String username = jwtService.extractUsername(jwt);
                
                if (username != null) {
                    try {
                        // Load user details
                        UserDetails userDetails = this.userDetailsService.loadUserByUsername(username);
                        
                        // Validate token against user details
                        if (jwtService.isTokenValid(jwt, userDetails)) {
                            // Create authentication token
                            UsernamePasswordAuthenticationToken authToken = new UsernamePasswordAuthenticationToken(
                                    userDetails,
                                    null,
                                    userDetails.getAuthorities()
                            );
                            authToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                            
                            // Set authentication in security context
                            SecurityContextHolder.getContext().setAuthentication(authToken);
                            logger.debug("Successfully authenticated user: {}", username);
                        } else {
                            logger.debug("JWT token validation failed for user: {}", username);
                        }
                    } catch (Exception e) {
                        logger.debug("Error loading user details for: {}", username, e);
                    }
                }
            }
        } catch (Exception e) {
            logger.error("Error processing JWT authentication: {}", e.getMessage());
        }

        filterChain.doFilter(request, response);
    }

    /**
     * Extract JWT token from cookie or Authorization header
     */
    private String extractJwtToken(HttpServletRequest request) {
        // First try to get token from cookie
        String tokenFromCookie = extractTokenFromCookie(request);
        if (tokenFromCookie != null) {
            logger.debug("Using JWT token from cookie");
            return tokenFromCookie;
        }

        // Fall back to Authorization header
        String authorizationHeader = request.getHeader("Authorization");
        if (authorizationHeader != null && authorizationHeader.startsWith("Bearer ")) {
            logger.debug("Using JWT token from Authorization header");
            return authorizationHeader.substring(7);
        }

        return null;
    }

    /**
     * Extract JWT token from cookie
     */
    private String extractTokenFromCookie(HttpServletRequest request) {
        Cookie[] cookies = request.getCookies();
        if (cookies != null) {
            for (Cookie cookie : cookies) {
                if (JWT_COOKIE_NAME.equals(cookie.getName())) {
                    String token = cookie.getValue();
                    if (token != null && !token.trim().isEmpty()) {
                        return token;
                    }
                }
            }
        }
        return null;
    }

    /**
     * Check if the request path is for a public endpoint that doesn't require authentication
     */
    private boolean isPublicEndpoint(String path) {
        return path.startsWith("/api/auth/register") ||
               path.startsWith("/api/auth/login") ||
               path.startsWith("/api/auth/verify-email") ||
               path.startsWith("/api/auth/profile") ||
               path.startsWith("/api/v1/health") ||
               path.startsWith("/api/v1/get_analysis") ||
               path.startsWith("/swagger-ui/") ||
               path.startsWith("/api-docs") ||
               path.equals("/swagger-ui.html");
    }
} 