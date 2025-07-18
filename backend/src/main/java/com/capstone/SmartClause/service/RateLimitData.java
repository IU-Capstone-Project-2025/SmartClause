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
     * Remove the most recent request from tracking.
     * This is used for refunding rate limit consumption when a request
     * should not count against the limit (e.g., duplicate uploads).
     */
    public void removeLatestRequest() {
        if (!requestTimestamps.isEmpty()) {
            // Remove the most recent request (last added)
            // Since we can't remove from the tail of ConcurrentLinkedQueue efficiently,
            // we'll convert to array, remove last, and rebuild
            LocalDateTime[] timestamps = requestTimestamps.toArray(new LocalDateTime[0]);
            if (timestamps.length > 0) {
                requestTimestamps.clear();
                // Add back all except the last one
                for (int i = 0; i < timestamps.length - 1; i++) {
                    requestTimestamps.offer(timestamps[i]);
                }
            }
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