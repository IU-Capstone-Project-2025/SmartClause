package com.capstone.SmartClause.repository;

import com.capstone.SmartClause.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface UserRepository extends JpaRepository<User, UUID> {
    
    // Find user by username (for login)
    Optional<User> findByUsername(String username);
    
    // Find user by email (for login and registration validation)
    Optional<User> findByEmail(String email);
    
    // Find user by username or email (for flexible login)
    @Query("SELECT u FROM User u WHERE u.username = :usernameOrEmail OR u.email = :usernameOrEmail")
    Optional<User> findByUsernameOrEmail(@Param("usernameOrEmail") String usernameOrEmail);
    
    // Check if username exists (for registration validation)
    boolean existsByUsername(String username);
    
    // Check if email exists (for registration validation)
    boolean existsByEmail(String email);
    
    // Find user by email verification token
    Optional<User> findByEmailVerificationToken(String token);
    
    // Find user by password reset token
    Optional<User> findByPasswordResetToken(String token);
    
    // Find users by role
    List<User> findByRole(User.UserRole role);
    
    // Find active users
    List<User> findByIsActiveTrue();
    
    // Find verified users
    List<User> findByIsEmailVerifiedTrue();
    
    // Find users created after a certain date
    List<User> findByCreatedAtAfter(LocalDateTime date);
    
    // Find users who logged in recently
    List<User> findByLastLoginAtAfter(LocalDateTime date);
    
    // Find users with expired password reset tokens
    @Query("SELECT u FROM User u WHERE u.passwordResetToken IS NOT NULL AND u.passwordResetExpiresAt < :now")
    List<User> findUsersWithExpiredPasswordResetTokens(@Param("now") LocalDateTime now);
    
    // Count active users
    long countByIsActiveTrue();
    
    // Count verified users  
    long countByIsEmailVerifiedTrue();
    
    // Count users by role
    long countByRole(User.UserRole role);
} 