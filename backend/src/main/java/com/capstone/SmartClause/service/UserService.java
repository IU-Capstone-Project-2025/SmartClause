package com.capstone.SmartClause.service;

import com.capstone.SmartClause.model.User;
import com.capstone.SmartClause.model.dto.AuthDto;
import com.capstone.SmartClause.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;

@Service
@Transactional
public class UserService implements UserDetailsService {

    private static final Logger logger = LoggerFactory.getLogger(UserService.class);

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;

    // Constructor injection - NO circular dependency
    public UserService(UserRepository userRepository, 
                      PasswordEncoder passwordEncoder,
                      JwtService jwtService) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
    }

    /**
     * Load user by username for Spring Security
     */
    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        User user = userRepository.findByUsernameOrEmail(username)
                .orElseThrow(() -> new UsernameNotFoundException("User not found: " + username));
        
        logger.debug("Loaded user: {} with authorities: {}", username, user.getAuthorities());
        return user;
    }

    /**
     * Register a new user
     */
    public AuthDto.RegisterResponse registerUser(AuthDto.RegisterRequest request) {
        logger.info("Registering new user: {}", request.getUsername());

        // Check if username already exists
        if (userRepository.existsByUsername(request.getUsername())) {
            throw new IllegalArgumentException("Username already exists: " + request.getUsername());
        }

        // Check if email already exists
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new IllegalArgumentException("Email already exists: " + request.getEmail());
        }

        // Create new user
        User user = new User();
        user.setUsername(request.getUsername());
        user.setEmail(request.getEmail());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setFirstName(request.getFirstName());
        user.setLastName(request.getLastName());
        user.setRole(User.UserRole.USER);
        user.setIsActive(true);
        user.setIsEmailVerified(false); // Require email verification
        user.setEmailVerificationToken(generateVerificationToken());

        User savedUser = userRepository.save(user);
        logger.info("User registered successfully: {}", savedUser.getUsername());

        // TODO: Send email verification email

        return new AuthDto.RegisterResponse(
            "User registered successfully. Please check your email for verification.",
            convertToUserInfo(savedUser),
            true
        );
    }

    /**
     * Authenticate user and generate JWT token - Manual authentication without AuthenticationManager
     */
    public AuthDto.AuthResponse authenticateUser(AuthDto.LoginRequest request) {
        logger.info("Authenticating user: {}", request.getUsernameOrEmail());

        // Load user details manually
        User user = userRepository.findByUsernameOrEmail(request.getUsernameOrEmail())
                .orElseThrow(() -> new UsernameNotFoundException("Invalid username or email"));

        // Verify password manually using PasswordEncoder
        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new IllegalArgumentException("Invalid password");
        }

        // Check if user is active
        if (!user.getIsActive()) {
            throw new IllegalArgumentException("Account is deactivated");
        }

        // Update last login time
        user.setLastLoginAt(LocalDateTime.now());
        userRepository.save(user);

        // Generate JWT token
        String token = jwtService.generateToken(user);
        
        logger.info("User authenticated successfully: {}", user.getUsername());

        return new AuthDto.AuthResponse(
            token,
            "Bearer",
            jwtService.getExpirationTime(),
            convertToUserInfo(user)
        );
    }

    /**
     * Change user password
     */
    public AuthDto.MessageResponse changePassword(String userId, AuthDto.ChangePasswordRequest request) {
        logger.info("Changing password for user: {}", userId);

        User user = userRepository.findById(UUID.fromString(userId))
                .orElseThrow(() -> new UsernameNotFoundException("User not found"));

        // Verify current password
        if (!passwordEncoder.matches(request.getCurrentPassword(), user.getPassword())) {
            throw new IllegalArgumentException("Current password is incorrect");
        }

        // Update password
        user.setPassword(passwordEncoder.encode(request.getNewPassword()));
        userRepository.save(user);

        logger.info("Password changed successfully for user: {}", userId);
        return new AuthDto.MessageResponse("Password changed successfully");
    }

    /**
     * Verify email with token
     */
    public AuthDto.MessageResponse verifyEmail(String token) {
        logger.info("Verifying email with token");

        User user = userRepository.findByEmailVerificationToken(token)
                .orElseThrow(() -> new IllegalArgumentException("Invalid verification token"));

        user.setIsEmailVerified(true);
        user.setEmailVerificationToken(null);
        userRepository.save(user);

        logger.info("Email verified successfully for user: {}", user.getUsername());
        return new AuthDto.MessageResponse("Email verified successfully");
    }

    /**
     * Get user profile information
     */
    public AuthDto.UserInfo getUserProfile(String userId) {
        User user = userRepository.findById(UUID.fromString(userId))
                .orElseThrow(() -> new UsernameNotFoundException("User not found"));
        
        return convertToUserInfo(user);
    }

    /**
     * Update user profile
     */
    public AuthDto.UserInfo updateUserProfile(String userId, AuthDto.RegisterRequest request) {
        logger.info("Updating profile for user: {}", userId);

        User user = userRepository.findById(UUID.fromString(userId))
                .orElseThrow(() -> new UsernameNotFoundException("User not found"));

        // Check if new username is taken by another user
        if (!user.getUsername().equals(request.getUsername()) && 
            userRepository.existsByUsername(request.getUsername())) {
            throw new IllegalArgumentException("Username already exists: " + request.getUsername());
        }

        // Check if new email is taken by another user
        if (!user.getEmail().equals(request.getEmail()) && 
            userRepository.existsByEmail(request.getEmail())) {
            throw new IllegalArgumentException("Email already exists: " + request.getEmail());
        }

        // Update user fields
        user.setUsername(request.getUsername());
        user.setEmail(request.getEmail());
        user.setFirstName(request.getFirstName());
        user.setLastName(request.getLastName());

        // If email changed, require re-verification
        if (!user.getEmail().equals(request.getEmail())) {
            user.setIsEmailVerified(false);
            user.setEmailVerificationToken(generateVerificationToken());
            // TODO: Send new verification email
        }

        User updatedUser = userRepository.save(user);
        logger.info("Profile updated successfully for user: {}", userId);

        return convertToUserInfo(updatedUser);
    }

    /**
     * Deactivate user account
     */
    public AuthDto.MessageResponse deactivateAccount(String userId) {
        logger.info("Deactivating account for user: {}", userId);

        User user = userRepository.findById(UUID.fromString(userId))
                .orElseThrow(() -> new UsernameNotFoundException("User not found"));

        user.setIsActive(false);
        userRepository.save(user);

        logger.info("Account deactivated for user: {}", userId);
        return new AuthDto.MessageResponse("Account deactivated successfully");
    }

    /**
     * Find user by ID
     */
    public Optional<User> findById(UUID userId) {
        return userRepository.findById(userId);
    }

    /**
     * Find user by username
     */
    public Optional<User> findByUsername(String username) {
        return userRepository.findByUsername(username);
    }

    /**
     * Convert User entity to UserInfo DTO
     */
    private AuthDto.UserInfo convertToUserInfo(User user) {
        return new AuthDto.UserInfo(
            user.getId().toString(),
            user.getUsername(),
            user.getEmail(),
            user.getFirstName(),
            user.getLastName(),
            user.getFullName(),
            user.getRole().name(),
            user.getIsEmailVerified(),
            user.getCreatedAt(),
            user.getLastLoginAt()
        );
    }

    /**
     * Generate email verification token
     */
    private String generateVerificationToken() {
        return UUID.randomUUID().toString();
    }
} 