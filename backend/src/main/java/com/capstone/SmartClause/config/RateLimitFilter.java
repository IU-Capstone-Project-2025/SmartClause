package com.capstone.SmartClause.config;

import com.capstone.SmartClause.service.RateLimitService;
import com.capstone.SmartClause.util.AuthUtils;
import com.capstone.SmartClause.util.UserIdentificationUtils;
import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;

import java.io.IOException;

public class RateLimitFilter implements Filter {
    
    private static final Logger logger = LoggerFactory.getLogger(RateLimitFilter.class);
    
    private final RateLimitService rateLimitService;
    private final RateLimitConfig rateLimitConfig;
    private final UserIdentificationUtils userIdentificationUtils;
    private final AuthUtils authUtils;
    
    @Autowired
    public RateLimitFilter(RateLimitService rateLimitService, 
                          RateLimitConfig rateLimitConfig,
                          UserIdentificationUtils userIdentificationUtils,
                          AuthUtils authUtils) {
        this.rateLimitService = rateLimitService;
        this.rateLimitConfig = rateLimitConfig;
        this.userIdentificationUtils = userIdentificationUtils;
        this.authUtils = authUtils;
    }
    
    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) 
            throws IOException, ServletException {
        
        HttpServletRequest httpRequest = (HttpServletRequest) request;
        HttpServletResponse httpResponse = (HttpServletResponse) response;
        
        String requestPath = httpRequest.getServletPath();
        String method = httpRequest.getMethod();
        
        // CRITICAL FIX: Prevent duplicate rate limiting for the same request
        String rateLimitProcessedKey = "RATE_LIMIT_PROCESSED";
        if (httpRequest.getAttribute(rateLimitProcessedKey) != null) {
            logger.debug("Request already processed by rate limiter, skipping: {} {}", method, requestPath);
            chain.doFilter(request, response);
            return;
        }
        
        // Only apply rate limiting to specific endpoints that could be abused
        if (shouldApplyRateLimit(requestPath, method)) {
            
            // Mark this request as processed to prevent duplicate rate limiting
            httpRequest.setAttribute(rateLimitProcessedKey, true);
            
            logger.info("Applying rate limit to request: {} {}", method, requestPath);
            
            // Extract user ID from authentication
            String authorizationHeader = httpRequest.getHeader("Authorization");
            String userId = authUtils.extractUserIdFromRequest(httpRequest, authorizationHeader);
            
            // Generate unique identifier for rate limiting
            String userIdentifier = userIdentificationUtils.generateUserIdentifier(httpRequest, userId);
            boolean isAuthenticated = userIdentificationUtils.isAuthenticatedUser(userIdentifier);
            
            // Check rate limit
            RateLimitService.RateLimitResult result = rateLimitService.checkRateLimit(userIdentifier, isAuthenticated);
            
            if (!result.isAllowed()) {
                logger.warn("Rate limit exceeded for user {} on {} {}: minute={}, hour={}, day={}", 
                           userIdentifier, method, requestPath, 
                           result.getMinuteCount(), result.getHourCount(), result.getDayCount());
                
                handleRateLimitExceeded(httpResponse, userIdentifier, isAuthenticated);
                return;
            }
            
            // Add rate limit headers to response
            addRateLimitHeaders(httpResponse, userIdentifier, isAuthenticated, result);
            
            logger.debug("Request allowed for user {}: minute={}, hour={}, day={}", 
                        userIdentifier, result.getMinuteCount(), result.getHourCount(), result.getDayCount());
        } else {
            logger.debug("Skipping rate limit for request: {} {}", method, requestPath);
        }
        
        // Continue with the request
        chain.doFilter(request, response);
    }
    
    /**
     * Determine if rate limiting should be applied to this request.
     * Only apply to document analysis related endpoints that could be abused.
     */
    private boolean shouldApplyRateLimit(String requestPath, String method) {
        if (!rateLimitConfig.isEnabled()) {
            return false;
        }
        
        // Public analysis endpoint - main target for rate limiting
        if ("POST".equals(method) && "/api/v1/get_analysis".equals(requestPath)) {
            logger.debug("Rate limiting /api/v1/get_analysis endpoint");
            return true;
        }
        
        // Document upload endpoint
        if ("POST".equals(method) && requestPath.matches("/api/spaces/[^/]+/documents")) {
            logger.debug("Rate limiting document upload endpoint: {}", requestPath);
            return true;
        }
        
        // Document reanalysis endpoint  
        if ("POST".equals(method) && requestPath.matches("/api/documents/[^/]+/reanalyze")) {
            logger.debug("Rate limiting document reanalysis endpoint: {}", requestPath);
            return true;
        }
        
        // DO NOT rate limit authentication endpoints - users need to be able to register/login
        // DO NOT rate limit health checks, swagger, or other non-analysis endpoints
        
        return false;
    }
    
    /**
     * Handle rate limit exceeded scenario.
     */
    private void handleRateLimitExceeded(HttpServletResponse response, String userIdentifier, boolean isAuthenticated) 
            throws IOException {
        
        // Get remaining requests for better error messaging
        RateLimitService.RateLimitRemaining remaining = rateLimitService.getRemainingRequests(userIdentifier, isAuthenticated);
        
        response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        
        // Add rate limit headers
        addRateLimitHeaders(response, userIdentifier, isAuthenticated, null);
        
        // Add Retry-After header (suggest retry in 1 minute)
        response.setHeader("Retry-After", "60");
        
        // Create JSON error response
        String errorMessage = String.format(
            "{\"error\":\"Rate limit exceeded\",\"message\":\"Too many requests. Please try again later.\",\"remaining\":{\"minute\":%d,\"hour\":%d,\"day\":%d},\"retryAfter\":60}",
            remaining.getMinuteRemaining(),
            remaining.getHourRemaining(),
            remaining.getDayRemaining()
        );
        
        response.getWriter().write(errorMessage);
        response.getWriter().flush();
    }
    
    /**
     * Add rate limit headers to the response.
     */
    private void addRateLimitHeaders(HttpServletResponse response, String userIdentifier, boolean isAuthenticated, 
                                   RateLimitService.RateLimitResult currentResult) {
        
        // Get current limits based on authentication status
        int minuteLimit = isAuthenticated ? 
            rateLimitConfig.getAuthenticated().getRequestsPerMinute() : 
            rateLimitConfig.getAnonymous().getRequestsPerMinute();
        int hourLimit = isAuthenticated ? 
            rateLimitConfig.getAuthenticated().getRequestsPerHour() : 
            rateLimitConfig.getAnonymous().getRequestsPerHour();
        int dayLimit = isAuthenticated ? 
            rateLimitConfig.getAuthenticated().getRequestsPerDay() : 
            rateLimitConfig.getAnonymous().getRequestsPerDay();
        
        // Get remaining requests
        RateLimitService.RateLimitRemaining remaining = rateLimitService.getRemainingRequests(userIdentifier, isAuthenticated);
        
        // Add standard rate limit headers
        response.setHeader("X-RateLimit-Limit-Minute", String.valueOf(minuteLimit));
        response.setHeader("X-RateLimit-Limit-Hour", String.valueOf(hourLimit));
        response.setHeader("X-RateLimit-Limit-Day", String.valueOf(dayLimit));
        
        response.setHeader("X-RateLimit-Remaining-Minute", String.valueOf(remaining.getMinuteRemaining()));
        response.setHeader("X-RateLimit-Remaining-Hour", String.valueOf(remaining.getHourRemaining()));
        response.setHeader("X-RateLimit-Remaining-Day", String.valueOf(remaining.getDayRemaining()));
        
        // Add current usage if available
        if (currentResult != null) {
            response.setHeader("X-RateLimit-Used-Minute", String.valueOf(currentResult.getMinuteCount()));
            response.setHeader("X-RateLimit-Used-Hour", String.valueOf(currentResult.getHourCount()));
            response.setHeader("X-RateLimit-Used-Day", String.valueOf(currentResult.getDayCount()));
        }
        
        // Add user type header for debugging
        response.setHeader("X-RateLimit-User-Type", isAuthenticated ? "authenticated" : "anonymous");
    }
    
    @Override
    public void init(FilterConfig filterConfig) {
        logger.info("Rate limiting filter initialized");
    }
    
    @Override
    public void destroy() {
        logger.info("Rate limiting filter destroyed");
    }
} 