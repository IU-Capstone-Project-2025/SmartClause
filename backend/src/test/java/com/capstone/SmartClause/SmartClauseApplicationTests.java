package com.capstone.SmartClause;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

import com.capstone.SmartClause.service.ChatService;
import com.capstone.SmartClause.model.dto.ChatDto;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@Testcontainers
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class SmartClauseApplicationTests {
    @Container
    static PostgreSQLContainer<?> postgres =
        new PostgreSQLContainer<>("postgres:13-alpine")
            .withDatabaseName("test")
            .withUsername("test")
            .withPassword("test");

    @DynamicPropertySource
    static void registerPgProps(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ChatService chatService;

    @Test
    void healthCheck() throws Exception {
        // Mock ChatService to return healthy response
        ChatDto.ChatHealthResponse healthResponse = new ChatDto.ChatHealthResponse();
        healthResponse.setStatus("healthy");
        healthResponse.setVersion("1.0.0");
        healthResponse.setDatabaseConnected(true);
        healthResponse.setAnalyzerConnected(true);
        healthResponse.setBackendConnected(true);
        
        when(chatService.checkChatHealth()).thenReturn(healthResponse);
        
        mockMvc.perform(get("/api/v1/health"))
                .andExpect(status().isOk());
    }
}
