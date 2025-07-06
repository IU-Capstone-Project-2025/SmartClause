package com.capstone.SmartClause.service;

import com.capstone.SmartClause.model.dto.ChatDto;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

import java.util.Map;

@Service
public class ChatService {

    private static final Logger logger = LoggerFactory.getLogger(ChatService.class);

    @Value("${chat.api.baseUrl:http://chat:8002}")
    private String chatApiUrl;

    @Autowired
    private RestTemplate restTemplate;

    /**
     * Check chat service health
     */
    public ChatDto.ChatHealthResponse checkChatHealth() {
        try {
            String url = chatApiUrl + "/api/v1/health";
            logger.debug("Checking chat service health: {}", url);

            ResponseEntity<ChatDto.ChatHealthResponse> response = restTemplate.exchange(
                url,
                HttpMethod.GET,
                null,
                ChatDto.ChatHealthResponse.class
            );

            return response.getBody();
        } catch (Exception e) {
            logger.error("Error checking chat service health", e);
            // Return unhealthy status
            ChatDto.ChatHealthResponse healthResponse = new ChatDto.ChatHealthResponse();
            healthResponse.setStatus("unhealthy");
            healthResponse.setVersion("unknown");
            healthResponse.setDatabaseConnected(false);
            healthResponse.setAnalyzerConnected(false);
            healthResponse.setBackendConnected(false);
            return healthResponse;
        }
    }

    /**
     * Get chat messages for a space
     */
    public ChatDto.GetMessagesResponse getMessages(String spaceId, int limit, int offset, String authorization) {
        try {
            String url = UriComponentsBuilder.fromHttpUrl(chatApiUrl + "/api/v1/spaces/{spaceId}/messages")
                .queryParam("limit", limit)
                .queryParam("offset", offset)
                .buildAndExpand(spaceId)
                .toUriString();

            HttpHeaders headers = createHeaders(authorization);
            HttpEntity<?> entity = new HttpEntity<>(headers);

            logger.debug("Getting messages from chat service: {}", url);

            ResponseEntity<ChatDto.GetMessagesResponse> response = restTemplate.exchange(
                url,
                HttpMethod.GET,
                entity,
                ChatDto.GetMessagesResponse.class
            );

            return response.getBody();
        } catch (Exception e) {
            logger.error("Error getting messages from chat service for space: {}", spaceId, e);
            throw new RuntimeException("Failed to get messages from chat service", e);
        }
    }

    /**
     * Send a message to space chat
     */
    public ChatDto.SendMessageResponse sendMessage(String spaceId, ChatDto.SendMessageRequest request, String authorization) {
        try {
            String url = chatApiUrl + "/api/v1/spaces/" + spaceId + "/messages";

            HttpHeaders headers = createHeaders(authorization);
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<ChatDto.SendMessageRequest> entity = new HttpEntity<>(request, headers);

            logger.debug("Sending message to chat service: {}", url);

            ResponseEntity<ChatDto.SendMessageResponse> response = restTemplate.exchange(
                url,
                HttpMethod.POST,
                entity,
                ChatDto.SendMessageResponse.class
            );

            return response.getBody();
        } catch (Exception e) {
            logger.error("Error sending message to chat service for space: {}", spaceId, e);
            throw new RuntimeException("Failed to send message to chat service", e);
        }
    }

    /**
     * Get chat session information for a space
     */
    public ChatDto.ChatSessionResponse getChatSession(String spaceId, String authorization) {
        try {
            String url = chatApiUrl + "/api/v1/spaces/" + spaceId + "/session";

            HttpHeaders headers = createHeaders(authorization);
            HttpEntity<?> entity = new HttpEntity<>(headers);

            logger.debug("Getting chat session from chat service: {}", url);

            ResponseEntity<ChatDto.ChatSessionResponse> response = restTemplate.exchange(
                url,
                HttpMethod.GET,
                entity,
                ChatDto.ChatSessionResponse.class
            );

            return response.getBody();
        } catch (Exception e) {
            logger.error("Error getting chat session from chat service for space: {}", spaceId, e);
            throw new RuntimeException("Failed to get chat session from chat service", e);
        }
    }

    /**
     * Update memory length for chat session
     */
    public ChatDto.ChatSessionResponse updateMemoryLength(String spaceId, ChatDto.ChatMemoryConfigRequest request, String authorization) {
        try {
            String url = chatApiUrl + "/api/v1/spaces/" + spaceId + "/session/memory";

            HttpHeaders headers = createHeaders(authorization);
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<ChatDto.ChatMemoryConfigRequest> entity = new HttpEntity<>(request, headers);

            logger.debug("Updating memory length in chat service: {}", url);

            ResponseEntity<ChatDto.ChatSessionResponse> response = restTemplate.exchange(
                url,
                HttpMethod.PUT,
                entity,
                ChatDto.ChatSessionResponse.class
            );

            return response.getBody();
        } catch (Exception e) {
            logger.error("Error updating memory length in chat service for space: {}", spaceId, e);
            throw new RuntimeException("Failed to update memory length in chat service", e);
        }
    }

    /**
     * Create HTTP headers with authorization
     */
    private HttpHeaders createHeaders(String authorization) {
        HttpHeaders headers = new HttpHeaders();
        if (authorization != null && !authorization.trim().isEmpty()) {
            headers.set("Authorization", authorization);
        }
        return headers;
    }
} 