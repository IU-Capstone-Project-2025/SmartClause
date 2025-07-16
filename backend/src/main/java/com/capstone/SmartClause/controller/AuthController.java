package com.capstone.SmartClause.controller;

import com.capstone.SmartClause.model.dto.AuthDto;
import com.capstone.SmartClause.service.UserService;
import com.capstone.SmartClause.service.JwtService;
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
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.Map;

@RestController
@RequestMapping("/api/auth")
@CrossOrigin(origins = "*", methods = {RequestMethod.GET, RequestMethod.POST, RequestMethod.PUT, RequestMethod.DELETE}, maxAge = 3600)
@Tag(name = "Authentication API", description = "User registration and authentication endpoints")
public class AuthController {

    private static final Logger logger = LoggerFactory.getLogger(AuthController.class);

    @Autowired
    private UserService userService;
    
    @Autowired
    private AuthUtils authUtils;
    
    @Autowired
    private JwtService jwtService;

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

    @Operation(summary = "User login", description = "Authenticate user and receive JWT token in cookie")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Login successful",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = AuthDto.AuthResponse.class))),
        @ApiResponse(responseCode = "401", description = "Invalid credentials",
                content = @Content(mediaType = "application/json")),
        @ApiResponse(responseCode = "400", description = "Invalid request data",
                content = @Content(mediaType = "application/json"))
    })
    @PostMapping("/login")
    public ResponseEntity<?> login(@Valid @RequestBody AuthDto.LoginRequest request, HttpServletResponse response) {
        try {
            AuthDto.AuthResponse authResponse = userService.authenticateUser(request);
            
            // Set JWT token as HTTP-only cookie
            Cookie jwtCookie = new Cookie("smartclause_token", authResponse.getAccessToken());
            jwtCookie.setHttpOnly(true);
            jwtCookie.setSecure(false); // Set to true in production with HTTPS
            jwtCookie.setMaxAge((int) authResponse.getExpiresIn()); // Cookie expires with token
            jwtCookie.setPath("/");
            // Note: SameSite=Lax is the default behavior in modern browsers
            response.addCookie(jwtCookie);
            
            // Return response without exposing the token in JSON (for security)
            // Create a copy without the access token
            AuthDto.AuthResponse sanitizedResponse = new AuthDto.AuthResponse();
            sanitizedResponse.setTokenType(authResponse.getTokenType());
            sanitizedResponse.setExpiresIn(authResponse.getExpiresIn());
            sanitizedResponse.setUser(authResponse.getUser());
            // accessToken is intentionally not set (remains null) for security
            
            return ResponseEntity.ok(sanitizedResponse);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                .body(Map.of("error", "Authentication failed: " + e.getMessage()));
        }
    }

    @Operation(summary = "User logout", description = "Clear authentication cookie and logout user")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Logout successful",
                content = @Content(mediaType = "application/json", schema = @Schema(implementation = AuthDto.MessageResponse.class)))
    })
    @PostMapping("/logout")
    public ResponseEntity<?> logout(HttpServletResponse response) {
        try {
            // Clear the JWT cookie
            Cookie jwtCookie = new Cookie("smartclause_token", "");
            jwtCookie.setHttpOnly(true);
            jwtCookie.setMaxAge(0); // Expire immediately
            jwtCookie.setPath("/");
            response.addCookie(jwtCookie);
            
            return ResponseEntity.ok(Map.of("message", "Logout successful"));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Logout failed: " + e.getMessage()));
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
            HttpServletRequest request,
            @Parameter(description = "Authorization header (optional, will try cookies first)") @RequestHeader(value = "Authorization", required = false) String authorization) {
        
        try {
            logger.info("Profile endpoint called with Authorization: {}", authorization != null ? "[PRESENT]" : "[NULL]");
            
            // First check if it's a system token (for service account access)
            if (authorization != null && authorization.startsWith("Bearer ")) {
                String token = authorization.substring(7);
                if (isValidSystemToken(token)) {
                    logger.info("Valid system token detected - returning system profile");
                    return ResponseEntity.ok(new AuthDto.UserInfo(
                        "system",
                        "system",
                        "system@smartclause.internal",
                        "System",
                        "Account",
                        "System Account",
                        "SYSTEM",
                        true,
                        null,
                        null
                    ));
                }
            }
            
            // Try to get user from cookie first, then from Authorization header
            String userId = authUtils.extractUserIdFromRequest(request, authorization);
            
            if (userId == null) {
                logger.warn("Authentication failed - no valid user ID found");
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }
            
            // Get user info from service
            AuthDto.UserInfo userInfo = userService.getUserProfile(userId);
            logger.info("Successfully retrieved profile for user: {}", userId);
            return ResponseEntity.ok(userInfo);
            
        } catch (Exception e) {
            logger.error("Error getting user profile: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Failed to get user profile: " + e.getMessage()));
        }
    }
    
    /**
     * Validate if a token is a valid system token by checking its claims
     */
    private boolean isValidSystemToken(String token) {
        try {
            String userId = jwtService.extractUserId(token);
            String role = jwtService.extractUserRole(token);
            
            return "system".equals(userId) && "SYSTEM".equals(role);
        } catch (Exception e) {
            logger.error("Error validating system token: {}", e.getMessage());
            return false;
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
            HttpServletRequest request,
            @Parameter(description = "Authorization header (optional, will try cookies first)") @RequestHeader(value = "Authorization", required = false) String authorization,
            @Valid @RequestBody AuthDto.RegisterRequest requestBody) {
        try {
            String userId = authUtils.extractUserIdFromRequest(request, authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }

            AuthDto.UserInfo userInfo = userService.updateUserProfile(userId, requestBody);
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
            HttpServletRequest request,
            @Parameter(description = "Authorization header (optional, will try cookies first)") @RequestHeader(value = "Authorization", required = false) String authorization,
            @Valid @RequestBody AuthDto.ChangePasswordRequest requestBody) {
        try {
            String userId = authUtils.extractUserIdFromRequest(request, authorization);
            if (userId == null) {
                return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(Map.of("error", "Authentication required"));
            }

            AuthDto.MessageResponse response = userService.changePassword(userId, requestBody);
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
            HttpServletRequest request,
            @Parameter(description = "Authorization header (optional, will try cookies first)") @RequestHeader(value = "Authorization", required = false) String authorization) {
        try {
            String userId = authUtils.extractUserIdFromRequest(request, authorization);
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