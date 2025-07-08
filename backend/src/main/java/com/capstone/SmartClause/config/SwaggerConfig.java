package com.capstone.SmartClause.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.servers.Server;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import io.swagger.v3.oas.models.Components;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
public class SwaggerConfig {

    private static final String BEARER_KEY_SECURITY_SCHEME = "bearer-key";

    @Bean
    public OpenAPI logsOpenAPI() {
        return new OpenAPI()
                .addSecurityItem(new SecurityRequirement().addList(BEARER_KEY_SECURITY_SCHEME))
                .components(new Components()
                        .addSecuritySchemes(BEARER_KEY_SECURITY_SCHEME, createAPIKeyScheme()))
                .info(new Info()
                    .title("SmartClause API")
                    .description("API for analyzing and processing legal documents")
                    .version("v1.0.0"))
                .servers(List.of(
                        new Server().url("/").description("Default Server URL")
                ));
    }

    private SecurityScheme createAPIKeyScheme() {
        return new SecurityScheme()
                .type(SecurityScheme.Type.HTTP)
                .bearerFormat("JWT")
                .scheme("bearer")
                .description("Enter JWT Bearer token only");
    }
}