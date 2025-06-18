package com.capstone.SmartClause.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.servers.Server;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI logsOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                    .title("SmartClause API")
                    .description("API for analyzing and processing legal documents")
                    .version("v1.0.0"))
                .servers(List.of(
                        new Server().url("/").description("Default Server URL")
                ));
    }
}