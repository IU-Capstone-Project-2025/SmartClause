package com.capstone.SmartClause.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties(prefix = "app.rate-limit")
@Data
public class RateLimitConfig {
    
    private boolean enabled = true;
    
    private Anonymous anonymous = new Anonymous();
    private Authenticated authenticated = new Authenticated();
    private Cache cache = new Cache();
    
    @Data
    public static class Anonymous {
        private int requestsPerMinute = 10;
        private int requestsPerHour = 50;
        private int requestsPerDay = 200;
    }
    
    @Data
    public static class Authenticated {
        private int requestsPerMinute = 60;
        private int requestsPerHour = 500;
        private int requestsPerDay = 2000;
    }
    
    @Data
    public static class Cache {
        private int expireMinutes = 60;
    }
} 