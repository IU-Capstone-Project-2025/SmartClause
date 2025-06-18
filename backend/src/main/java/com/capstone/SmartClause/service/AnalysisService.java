package com.capstone.SmartClause.service;

import com.capstone.SmartClause.model.AnalysisResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

@Service
public class AnalysisService {

    private static final Logger logger = LoggerFactory.getLogger(AnalysisService.class);

    @Value("${analyzer.api.baseUrl}")
    private String analyzerApiUrl;

    @Autowired
    private RestTemplate restTemplate;

    public AnalysisResponse analyzeDocument(String id, MultipartFile file) throws IOException {
        logger.info("Sending document for analysis: id={}, filename={}", id, file.getOriginalFilename());

        String analyzeUrl = analyzerApiUrl + "/analyze";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("id", id);
        body.add("file", new org.springframework.core.io.ByteArrayResource(file.getBytes()) {
            @Override
            public String getFilename() {
                return file.getOriginalFilename();
            }
        });

        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

        try {
            ResponseEntity<AnalysisResponse> response = restTemplate.exchange(
                    analyzeUrl,
                    HttpMethod.POST,
                    requestEntity,
                    AnalysisResponse.class
            );

            logger.info("Analysis completed successfully for document: {}", id);
            return response.getBody();
        } catch (Exception e) {
            logger.error("Error during document analysis: {}", e.getMessage(), e);
            throw new RuntimeException("Failed to process document: " + e.getMessage(), e);
        }
    }
}
