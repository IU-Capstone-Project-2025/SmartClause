package com.capstone.SmartClause.controller;

import com.capstone.SmartClause.model.dto.AuthDto;
import com.capstone.SmartClause.service.UserService;
import com.capstone.SmartClause.util.AuthUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;

import jakarta.validation.Valid;
import java.util.Map;

@RestController
@RequestMapping("/api/auth")
@CrossOrigin(origins = "*", methods = {RequestMethod.GET, RequestMethod.POST, RequestMethod.PUT, RequestMethod.DELETE}, maxAge = 3600)
@Tag(name = "Authentication API", description = "User registration and authentication endpoints")
public class AuthController {

    @Autowired
    private UserService userService;
    
    @Autowired
    private AuthUtils authUtils;

    @Operation(summary = "Register new user", description = "Register a new user account")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "201", description = "User registered successfully",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = AuthDto.RegisterResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid registration data",
                content = @Content(mediaType = "application/json")),
        @ApiResponse(responseCode = "409", description = "Username or email already exists",
                content = @Content(mediaType = "application/json"))
    })
    @PostMapping("/register")
    public ResponseEntity<?> register(@Valid @RequestBody AuthDto.RegisterRequest request) {
        try {
            AuthDto.RegisterResponse response = userService.registerUser(request);
            return ResponseEntity.status(HttpStatus.CREATED).body(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Registration failed: " + e.getMessage()));
        }
    }

    @Operation(summary = "User login", description = "Authenticate user and receive JWT token")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Login successful",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = AuthDto.AuthResponse.class))),
        @ApiResponse(responseCode = "401", description = "Invalid credentials",
                content = @Content(mediaType = "application/json")),
        @ApiResponse(responseCode = "400", description = "Invalid request data",
                content = @Content(mediaType = "application/json"))
    })
    @PostMapping("/login")
    public ResponseEntity<?> login(@Valid @RequestBody AuthDto.LoginRequest request) {
        try {
            AuthDto.AuthResponse response = userService.authenticateUser(request);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                .body(Map.of("error", "Authentication failed: " + e.getMessage()));
        }
    }

    @Operation(summary = "Get user profile", description = "Get current user profile information")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Profile retrieved successfully",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = AuthDto.UserInfo.class))),
        @ApiResponse(responseCode = "401", description = "Authentication required",
                content = @Content(mediaType = "application/json"))
    })
    @GetMapping("/profile")
    public ResponseEntity<?> getProfile(
            @Parameter(description = "Authorization header") @RequestHeader(value = "Authorization", required = false) String authorization) {
        try {
            String userId = authUtils.extractUserIdFromHeader(authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }

            AuthDto.UserInfo userInfo = userService.getUserProfile(userId);
            return ResponseEntity.ok(userInfo);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to retrieve profile: " + e.getMessage()));
        }
    }

    @Operation(summary = "Update user profile", description = "Update current user profile information")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Profile updated successfully",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = AuthDto.UserInfo.class))),
        @ApiResponse(responseCode = "401", description = "Authentication required",
                content = @Content(mediaType = "application/json")),
        @ApiResponse(responseCode = "409", description = "Username or email already exists",
                content = @Content(mediaType = "application/json"))
    })
    @PutMapping("/profile")
    public ResponseEntity<?> updateProfile(
            @Parameter(description = "Authorization header") @RequestHeader(value = "Authorization", required = false) String authorization,
            @Valid @RequestBody AuthDto.RegisterRequest request) {
        try {
            String userId = authUtils.extractUserIdFromHeader(authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }

            AuthDto.UserInfo userInfo = userService.updateUserProfile(userId, request);
            return ResponseEntity.ok(userInfo);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to update profile: " + e.getMessage()));
        }
    }

    @Operation(summary = "Change password", description = "Change user password")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Password changed successfully",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = AuthDto.MessageResponse.class))),
        @ApiResponse(responseCode = "401", description = "Authentication required",
                content = @Content(mediaType = "application/json")),
        @ApiResponse(responseCode = "400", description = "Invalid current password",
                content = @Content(mediaType = "application/json"))
    })
    @PutMapping("/change-password")
    public ResponseEntity<?> changePassword(
            @Parameter(description = "Authorization header") @RequestHeader(value = "Authorization", required = false) String authorization,
            @Valid @RequestBody AuthDto.ChangePasswordRequest request) {
        try {
            String userId = authUtils.extractUserIdFromHeader(authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }

            AuthDto.MessageResponse response = userService.changePassword(userId, request);
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to change password: " + e.getMessage()));
        }
    }

    @Operation(summary = "Verify email", description = "Verify user email with token")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Email verified successfully",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = AuthDto.MessageResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid verification token",
                content = @Content(mediaType = "application/json"))
    })
    @PostMapping("/verify-email")
    public ResponseEntity<?> verifyEmail(@Valid @RequestBody AuthDto.VerifyEmailRequest request) {
        try {
            AuthDto.MessageResponse response = userService.verifyEmail(request.getToken());
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Email verification failed: " + e.getMessage()));
        }
    }

    @Operation(summary = "Deactivate account", description = "Deactivate current user account")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Account deactivated successfully",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = AuthDto.MessageResponse.class))),
        @ApiResponse(responseCode = "401", description = "Authentication required",
                content = @Content(mediaType = "application/json"))
    })
    @DeleteMapping("/account")
    public ResponseEntity<?> deactivateAccount(
            @Parameter(description = "Authorization header") @RequestHeader(value = "Authorization", required = false) String authorization) {
        try {
            String userId = authUtils.extractUserIdFromHeader(authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }

            AuthDto.MessageResponse response = userService.deactivateAccount(userId);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to deactivate account: " + e.getMessage()));
        }
    }
} 