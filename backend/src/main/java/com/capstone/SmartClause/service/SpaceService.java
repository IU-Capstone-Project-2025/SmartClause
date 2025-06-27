package com.capstone.SmartClause.service;

import com.capstone.SmartClause.model.Space;
import com.capstone.SmartClause.model.dto.SpaceDto;
import com.capstone.SmartClause.repository.SpaceRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@Transactional
public class SpaceService {

    private static final Logger logger = LoggerFactory.getLogger(SpaceService.class);

    @Autowired
    private SpaceRepository spaceRepository;

    @Autowired
    private com.capstone.SmartClause.repository.DocumentRepository documentRepository;

    public List<SpaceDto.SpaceListItem> getAllSpaces() {
        logger.info("Fetching all spaces");
        List<Space> spaces = spaceRepository.findAllByOrderByCreatedAtDesc();
        
        return spaces.stream()
            .map(this::convertToSpaceListItem)
            .collect(Collectors.toList());
    }

    public List<SpaceDto.SpaceListItem> getSpacesByUser(String userId) {
        logger.info("Fetching spaces for user: {}", userId);
        List<Space> spaces = spaceRepository.findByUserIdOrderByCreatedAtDesc(userId);
        
        return spaces.stream()
            .map(this::convertToSpaceListItem)
            .collect(Collectors.toList());
    }

    public Optional<SpaceDto.SpaceDetailResponse> getSpaceById(UUID spaceId) {
        logger.info("Fetching space details for ID: {}", spaceId);
        
        Optional<Space> spaceOpt = spaceRepository.findByIdWithDocuments(spaceId);
        if (spaceOpt.isEmpty()) {
            return Optional.empty();
        }

        Space space = spaceOpt.get();
        SpaceDto.SpaceDetailResponse response = new SpaceDto.SpaceDetailResponse();
        response.setId(space.getId().toString());
        response.setName(space.getName());
        response.setDescription(space.getDescription());
        response.setCreatedAt(space.getCreatedAt());
        response.setDocuments(getDocumentListItemsBySpaceId(spaceId));

        return Optional.of(response);
    }

    public Optional<SpaceDto.SpaceDetailResponse> getSpaceByIdAndUser(UUID spaceId, String userId) {
        logger.info("Fetching space details for ID: {} and user: {}", spaceId, userId);
        
        Optional<Space> spaceOpt = spaceRepository.findByIdAndUserId(spaceId, userId);
        if (spaceOpt.isEmpty()) {
            return Optional.empty();
        }

        // For now, just return the same as getSpaceById since we don't have auth yet
        return getSpaceById(spaceId);
    }

    private List<com.capstone.SmartClause.model.dto.DocumentDto.DocumentListItem> getDocumentListItemsBySpaceId(UUID spaceId) {
        List<com.capstone.SmartClause.model.Document> documents = documentRepository.findBySpaceIdOrderByUploadedAtDesc(spaceId);
        
        return documents.stream()
            .map(this::convertToDocumentListItem)
            .collect(Collectors.toList());
    }

    private com.capstone.SmartClause.model.dto.DocumentDto.DocumentListItem convertToDocumentListItem(com.capstone.SmartClause.model.Document document) {
        com.capstone.SmartClause.model.dto.DocumentDto.DocumentListItem item = new com.capstone.SmartClause.model.dto.DocumentDto.DocumentListItem();
        item.setId(document.getId().toString());
        item.setName(document.getName());
        item.setStatus(document.getStatus().name().toLowerCase());
        item.setAnalysisSummary(generateAnalysisSummary(document));
        return item;
    }

    private String generateAnalysisSummary(com.capstone.SmartClause.model.Document document) {
        if (document.getStatus() == com.capstone.SmartClause.model.Document.DocumentStatus.COMPLETED) {
            return "Analysis completed - Found potential issues";
        } else if (document.getStatus() == com.capstone.SmartClause.model.Document.DocumentStatus.PROCESSING) {
            return "Analysis in progress...";
        } else if (document.getStatus() == com.capstone.SmartClause.model.Document.DocumentStatus.ERROR) {
            return "Analysis failed";
        }
        return "Pending analysis";
    }

    public void deleteDocumentsBySpaceId(UUID spaceId) {
        logger.info("Deleting all documents in space: {}", spaceId);
        List<com.capstone.SmartClause.model.Document> documents = documentRepository.findBySpaceIdOrderByUploadedAtDesc(spaceId);
        
        for (com.capstone.SmartClause.model.Document document : documents) {
            documentRepository.deleteById(document.getId());
        }
    }

    public SpaceDto.SpaceResponse createSpace(SpaceDto.CreateSpaceRequest request) {
        return createSpace(request, null); // No user for now
    }

    public SpaceDto.SpaceResponse createSpace(SpaceDto.CreateSpaceRequest request, String userId) {
        logger.info("Creating new space: {} for user: {}", request.getName(), userId);

        // Check for duplicate names (when we have user auth)
        if (userId != null && spaceRepository.existsByNameAndUserId(request.getName(), userId)) {
            throw new IllegalArgumentException("Space with name '" + request.getName() + "' already exists for this user");
        }

        Space space = new Space();
        space.setName(request.getName());
        space.setDescription(request.getDescription());
        space.setUserId(userId);
        space.setStatus(Space.SpaceStatus.ACTIVE);

        Space savedSpace = spaceRepository.save(space);
        logger.info("Created space with ID: {}", savedSpace.getId());

        return convertToSpaceResponse(savedSpace);
    }

    public Optional<SpaceDto.SpaceResponse> updateSpace(UUID spaceId, SpaceDto.UpdateSpaceRequest request) {
        return updateSpace(spaceId, request, null); // No user for now
    }

    public Optional<SpaceDto.SpaceResponse> updateSpace(UUID spaceId, SpaceDto.UpdateSpaceRequest request, String userId) {
        logger.info("Updating space: {} for user: {}", spaceId, userId);

        Optional<Space> spaceOpt = userId != null 
            ? spaceRepository.findByIdAndUserId(spaceId, userId)
            : spaceRepository.findById(spaceId);

        if (spaceOpt.isEmpty()) {
            return Optional.empty();
        }

        Space space = spaceOpt.get();
        
        if (request.getName() != null && !request.getName().trim().isEmpty()) {
            space.setName(request.getName().trim());
        }
        
        if (request.getDescription() != null) {
            space.setDescription(request.getDescription().trim());
        }

        Space updatedSpace = spaceRepository.save(space);
        logger.info("Updated space: {}", updatedSpace.getId());

        return Optional.of(convertToSpaceResponse(updatedSpace));
    }

    public boolean deleteSpace(UUID spaceId) {
        return deleteSpace(spaceId, null); // No user for now
    }

    public boolean deleteSpace(UUID spaceId, String userId) {
        logger.info("Deleting space: {} for user: {}", spaceId, userId);

        Optional<Space> spaceOpt = userId != null 
            ? spaceRepository.findByIdAndUserId(spaceId, userId)
            : spaceRepository.findById(spaceId);

        if (spaceOpt.isEmpty()) {
            return false;
        }

        // Delete all documents in the space first
        deleteDocumentsBySpaceId(spaceId);
        
        spaceRepository.deleteById(spaceId);
        logger.info("Deleted space: {}", spaceId);
        
        return true;
    }

    private SpaceDto.SpaceListItem convertToSpaceListItem(Space space) {
        SpaceDto.SpaceListItem item = new SpaceDto.SpaceListItem();
        item.setId(space.getId().toString());
        item.setName(space.getName());
        item.setDescription(space.getDescription());
        item.setCreatedAt(space.getCreatedAt());
        item.setDocumentsCount(space.getDocumentsCount());
        item.setStatus(space.getStatus().name().toLowerCase());
        return item;
    }

    private SpaceDto.SpaceResponse convertToSpaceResponse(Space space) {
        SpaceDto.SpaceResponse response = new SpaceDto.SpaceResponse();
        response.setId(space.getId().toString());
        response.setName(space.getName());
        response.setDescription(space.getDescription());
        response.setCreatedAt(space.getCreatedAt());
        return response;
    }
} 