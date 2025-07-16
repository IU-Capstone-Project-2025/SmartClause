package com.capstone.SmartClause.service;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.concurrent.ConcurrentLinkedQueue;

/**
 * Helper class to store rate limiting data for a user.
 * Tracks request timestamps and provides time window counting.
 */
public class RateLimitData {
    
    // Thread-safe queue to store request timestamps
    private final ConcurrentLinkedQueue<LocalDateTime> requestTimestamps = new ConcurrentLinkedQueue<>();
    
    /**
     * Record a new request at the given time.
     */
    public void recordRequest(LocalDateTime timestamp) {
        requestTimestamps.offer(timestamp);
    }
    
    /**
     * Get the count of requests within a specific time window.
     * 
     * @param currentTime Current time
     * @param unit Time unit (MINUTES, HOURS, DAYS)
     * @param amount Amount of time units to look back
     * @return Number of requests in the time window
     */
    public int getCountForTimeWindow(LocalDateTime currentTime, ChronoUnit unit, int amount) {
        LocalDateTime cutoffTime = currentTime.minus(amount, unit);
        
        // Count requests after the cutoff time
        return (int) requestTimestamps.stream()
                .filter(timestamp -> timestamp.isAfter(cutoffTime))
                .count();
    }
    
    /**
     * Remove old request timestamps that are no longer needed.
     * This keeps memory usage bounded by removing timestamps older than the longest time window we care about.
     */
    public void cleanupOldCounts(LocalDateTime currentTime) {
        // Remove timestamps older than 1 day + 1 hour buffer
        LocalDateTime cutoffTime = currentTime.minus(25, ChronoUnit.HOURS);
        
        // Remove old timestamps from the front of the queue
        while (!requestTimestamps.isEmpty() && 
               requestTimestamps.peek().isBefore(cutoffTime)) {
            requestTimestamps.poll();
        }
    }
    
    /**
     * Get the total number of recorded requests (for debugging).
     */
    public int getTotalRequestCount() {
        return requestTimestamps.size();
    }
    
    /**
     * Clear all recorded requests.
     */
    public void clear() {
        requestTimestamps.clear();
    }
} 