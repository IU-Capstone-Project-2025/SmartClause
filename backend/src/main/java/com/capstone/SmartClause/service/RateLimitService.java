package com.capstone.SmartClause.service;

import com.capstone.SmartClause.config.RateLimitConfig;
import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
import lombok.Data;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.concurrent.TimeUnit;

@Service
public class RateLimitService {
    
    private static final Logger logger = LoggerFactory.getLogger(RateLimitService.class);
    
    private final RateLimitConfig config;
    
    // Cache for storing rate limit data for each user
    private final Cache<String, RateLimitData> rateLimitCache;
    
    @Autowired
    public RateLimitService(RateLimitConfig config) {
        this.config = config;
        this.rateLimitCache = Caffeine.newBuilder()
                .maximumSize(10000) // Maximum number of users to track
                .expireAfterWrite(config.getCache().getExpireMinutes(), TimeUnit.MINUTES)
                .build();
        
        logger.info("Rate limiting service initialized with cache expiration: {} minutes", 
                    config.getCache().getExpireMinutes());
    }
    
    /**
     * Check if a request is allowed for the given user identifier.
     * 
     * @param userIdentifier Unique identifier for the user
     * @param isAuthenticated Whether the user is authenticated
     * @return RateLimitResult containing the decision and metadata
     */
    public RateLimitResult checkRateLimit(String userIdentifier, boolean isAuthenticated) {
        if (!config.isEnabled()) {
            logger.debug("Rate limiting is disabled, allowing request");
            return new RateLimitResult(true, 0, 0, 0);
        }
        
        RateLimitData userData = rateLimitCache.getIfPresent(userIdentifier);
        if (userData == null) {
            userData = new RateLimitData();
            rateLimitCache.put(userIdentifier, userData);
            logger.debug("Created new rate limit tracking for user: {}", userIdentifier);
        }
        
        LocalDateTime now = LocalDateTime.now();
        
        // Clean up old counts
        userData.cleanupOldCounts(now);
        
        // Get the appropriate limits based on authentication status
        int minuteLimit = isAuthenticated ? 
            config.getAuthenticated().getRequestsPerMinute() : 
            config.getAnonymous().getRequestsPerMinute();
        int hourLimit = isAuthenticated ? 
            config.getAuthenticated().getRequestsPerHour() : 
            config.getAnonymous().getRequestsPerHour();
        int dayLimit = isAuthenticated ? 
            config.getAuthenticated().getRequestsPerDay() : 
            config.getAnonymous().getRequestsPerDay();
        
        // Check current counts
        int minuteCount = userData.getCountForTimeWindow(now, ChronoUnit.MINUTES, 1);
        int hourCount = userData.getCountForTimeWindow(now, ChronoUnit.HOURS, 1);
        int dayCount = userData.getCountForTimeWindow(now, ChronoUnit.DAYS, 1);
        
        // Check if any limit is exceeded
        if (minuteCount > minuteLimit) {
            logger.warn("Rate limit exceeded for user {}: {} requests in last minute (limit: {})", 
                       userIdentifier, minuteCount, minuteLimit);
            return new RateLimitResult(false, minuteCount, hourCount, dayCount);
        }
        
        if (hourCount > hourLimit) {
            logger.warn("Rate limit exceeded for user {}: {} requests in last hour (limit: {})", 
                       userIdentifier, hourCount, hourLimit);
            return new RateLimitResult(false, minuteCount, hourCount, dayCount);
        }
        
        if (dayCount > dayLimit) {
            logger.warn("Rate limit exceeded for user {}: {} requests in last day (limit: {})", 
                       userIdentifier, dayCount, dayLimit);
            return new RateLimitResult(false, minuteCount, hourCount, dayCount);
        }
        
        // Allow the request and record it
        userData.recordRequest(now);
        
        logger.debug("Request allowed for user {}: minute={}/{}, hour={}/{}, day={}/{}", 
                    userIdentifier, minuteCount + 1, minuteLimit, hourCount + 1, hourLimit, dayCount + 1, dayLimit);
        
        return new RateLimitResult(true, minuteCount + 1, hourCount + 1, dayCount + 1);
    }
    
    /**
     * Get current usage statistics for a user.
     */
    public RateLimitResult getCurrentUsage(String userIdentifier, boolean isAuthenticated) {
        RateLimitData userData = rateLimitCache.getIfPresent(userIdentifier);
        if (userData == null) {
            return new RateLimitResult(true, 0, 0, 0);
        }
        
        LocalDateTime now = LocalDateTime.now();
        userData.cleanupOldCounts(now);
        
        int minuteCount = userData.getCountForTimeWindow(now, ChronoUnit.MINUTES, 1);
        int hourCount = userData.getCountForTimeWindow(now, ChronoUnit.HOURS, 1);
        int dayCount = userData.getCountForTimeWindow(now, ChronoUnit.DAYS, 1);
        
        return new RateLimitResult(true, minuteCount, hourCount, dayCount);
    }
    
    /**
     * Get remaining requests for a user.
     */
    public RateLimitRemaining getRemainingRequests(String userIdentifier, boolean isAuthenticated) {
        RateLimitResult current = getCurrentUsage(userIdentifier, isAuthenticated);
        
        int minuteLimit = isAuthenticated ? 
            config.getAuthenticated().getRequestsPerMinute() : 
            config.getAnonymous().getRequestsPerMinute();
        int hourLimit = isAuthenticated ? 
            config.getAuthenticated().getRequestsPerHour() : 
            config.getAnonymous().getRequestsPerHour();
        int dayLimit = isAuthenticated ? 
            config.getAuthenticated().getRequestsPerDay() : 
            config.getAnonymous().getRequestsPerDay();
        
        return new RateLimitRemaining(
            Math.max(0, minuteLimit - current.getMinuteCount()),
            Math.max(0, hourLimit - current.getHourCount()),
            Math.max(0, dayLimit - current.getDayCount())
        );
    }
    
    /**
     * Clear rate limit data for a user (useful for testing or admin operations).
     */
    public void clearUserRateLimit(String userIdentifier) {
        rateLimitCache.invalidate(userIdentifier);
        logger.info("Cleared rate limit data for user: {}", userIdentifier);
    }
    
    /**
     * Get cache statistics.
     */
    public String getCacheStats() {
        return String.format("Cache size: %d, Stats: %s", 
                           rateLimitCache.estimatedSize(), 
                           rateLimitCache.stats().toString());
    }
    
    @Data
    public static class RateLimitResult {
        private final boolean allowed;
        private final int minuteCount;
        private final int hourCount;
        private final int dayCount;
        
        public RateLimitResult(boolean allowed, int minuteCount, int hourCount, int dayCount) {
            this.allowed = allowed;
            this.minuteCount = minuteCount;
            this.hourCount = hourCount;
            this.dayCount = dayCount;
        }
    }
    
    @Data
    public static class RateLimitRemaining {
        private final int minuteRemaining;
        private final int hourRemaining;
        private final int dayRemaining;
        
        public RateLimitRemaining(int minuteRemaining, int hourRemaining, int dayRemaining) {
            this.minuteRemaining = minuteRemaining;
            this.hourRemaining = hourRemaining;
            this.dayRemaining = dayRemaining;
        }
    }
} 