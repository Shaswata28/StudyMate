"""
Authentication router for user registration, login, logout, and session management.

This module provides endpoints for:
- POST /api/auth/signup - User registration
- POST /api/auth/login - User login
- POST /api/auth/logout - User logout
- GET /api/auth/session - Get current session
- POST /api/auth/refresh - Refresh access token
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
import logging

from services.supabase_client import supabase_admin, get_anon_client, get_user_client
from services.auth_service import get_current_user, AuthUser
from models.schemas import (
    SignupRequest,
    LoginRequest,
    AuthResponse,
    RefreshTokenRequest,
    SessionResponse,
    MessageResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User successfully registered"},
        400: {"model": ErrorResponse, "description": "Invalid request or user already exists"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def signup(request: SignupRequest):
    """
    Register a new user with email and password.
    
    Creates a new user account in Supabase Auth. The user will receive
    an email verification link if email confirmation is enabled.
    
    Args:
        request: SignupRequest containing email and password
        
    Returns:
        AuthResponse: Access token, refresh token, and user information
        
    Raises:
        HTTPException: If registration fails (e.g., email already exists)
        
    Example:
        ```json
        POST /api/auth/signup
        {
            "email": "user@example.com",
            "password": "securepassword123"
        }
        ```
    """
    try:
        logger.info(f"Attempting to register user: {request.email}")
        
        # Use admin client for signup to auto-confirm email (for testing/development)
        # In production, you may want to use anon_client and require email confirmation
        # anon_client = get_anon_client()
        
        # Sign up the user with Supabase Auth using admin client (auto-confirms email)
        response = supabase_admin.auth.admin.create_user({
            "email": request.email,
            "password": request.password,
            "email_confirm": True  # Auto-confirm email for testing
        })
        
        if not response.user:
            logger.error("Signup failed: No user returned from Supabase")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User registration failed"
            )
        
        logger.info(f"User registered successfully: {response.user.id}")
        
        # Admin create_user doesn't return a session, so we need to sign in the user
        anon_client = get_anon_client()
        login_response = anon_client.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if not login_response.session:
            logger.error(f"Failed to create session after signup for user: {response.user.id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User created but failed to establish session"
            )
        
        # Return authentication response
        return AuthResponse(
            access_token=login_response.session.access_token,
            token_type="bearer",
            expires_in=login_response.session.expires_in or 3600,
            refresh_token=login_response.session.refresh_token,
            user={
                "id": response.user.id,
                "email": response.user.email,
                "created_at": response.user.created_at,
                "email_confirmed_at": response.user.email_confirmed_at
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.warning(f"Signup failed for {request.email}: {str(e)}")
        
        # Handle specific error cases
        error_msg = str(e).lower()
        if "already registered" in error_msg or "already exists" in error_msg or "user already registered" in error_msg or "already been registered" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists"
            )
        
        if "invalid" in error_msg or "password" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: {str(e)}"
            )
        
        # Generic error for unexpected cases
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration"
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={
        200: {"description": "User successfully logged in"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def login(request: LoginRequest):
    """
    Authenticate a user with email and password.
    
    Validates user credentials and returns JWT access token and refresh token
    for authenticated API requests.
    
    Args:
        request: LoginRequest containing email and password
        
    Returns:
        AuthResponse: Access token, refresh token, and user information
        
    Raises:
        HTTPException: If authentication fails (invalid credentials)
        
    Example:
        ```json
        POST /api/auth/login
        {
            "email": "user@example.com",
            "password": "securepassword123"
        }
        ```
    """
    try:
        logger.info(f"Login attempt for user: {request.email}")
        
        # Use anonymous client for login (no authentication required)
        anon_client = get_anon_client()
        
        # Authenticate with Supabase Auth
        response = anon_client.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if not response.user or not response.session:
            logger.warning(f"Login failed for {request.email}: No user or session returned")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        logger.info(f"User logged in successfully: {response.user.id}")
        
        # Return authentication response
        return AuthResponse(
            access_token=response.session.access_token,
            token_type="bearer",
            expires_in=response.session.expires_in or 3600,
            refresh_token=response.session.refresh_token,
            user={
                "id": response.user.id,
                "email": response.user.email,
                "created_at": response.user.created_at,
                "email_confirmed_at": response.user.email_confirmed_at,
                "last_sign_in_at": response.user.last_sign_in_at
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.warning(f"Login failed for {request.email}: {str(e)}")
        
        # Return generic error message for security (don't reveal if email exists)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


@router.post(
    "/logout",
    response_model=MessageResponse,
    responses={
        200: {"description": "User successfully logged out"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def logout(user: AuthUser = Depends(get_current_user)):
    """
    Log out the current user.
    
    Invalidates the user's current session and access token.
    The client should discard the access token and refresh token after logout.
    
    Args:
        user: Current authenticated user (from JWT token)
        
    Returns:
        MessageResponse: Success message
        
    Raises:
        HTTPException: If logout fails
        
    Headers:
        Authorization: Bearer <access_token>
        
    Example:
        ```
        POST /api/auth/logout
        Authorization: Bearer eyJhbGc...
        ```
    """
    try:
        logger.info(f"Logout attempt for user: {user.id}")
        
        # Use admin client to sign out the user's session
        # Note: In a real application, the client should discard tokens locally
        # The server-side logout is optional and mainly for session invalidation
        try:
            supabase_admin.auth.admin.sign_out(user.access_token)
        except Exception as e:
            # If admin sign_out fails, it's okay - the client will discard tokens
            logger.warning(f"Admin sign_out failed (non-critical): {str(e)}")
        
        logger.info(f"User logged out successfully: {user.id}")
        
        return MessageResponse(
            message="Successfully logged out"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.warning(f"Logout failed for user {user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get(
    "/session",
    response_model=SessionResponse,
    responses={
        200: {"description": "Current session information"},
        401: {"model": ErrorResponse, "description": "Not authenticated or session expired"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_session(user: AuthUser = Depends(get_current_user)):
    """
    Get current user session information.
    
    Returns information about the authenticated user and their current session.
    This endpoint can be used to verify if a token is still valid.
    
    Args:
        user: Current authenticated user (from JWT token)
        
    Returns:
        SessionResponse: User and session information
        
    Raises:
        HTTPException: If session retrieval fails
        
    Headers:
        Authorization: Bearer <access_token>
        
    Example:
        ```
        GET /api/auth/session
        Authorization: Bearer eyJhbGc...
        ```
    """
    try:
        logger.info(f"Session request for user: {user.id}")
        
        # Get user details from Supabase
        user_response = supabase_admin.auth.get_user(user.access_token)
        
        if not user_response.user:
            logger.warning(f"Session retrieval failed for user {user.id}: No user data")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalid"
            )
        
        logger.info(f"Session retrieved successfully for user: {user.id}")
        
        return SessionResponse(
            user={
                "id": user_response.user.id,
                "email": user_response.user.email,
                "created_at": user_response.user.created_at,
                "email_confirmed_at": user_response.user.email_confirmed_at,
                "last_sign_in_at": user_response.user.last_sign_in_at
            },
            session={
                "access_token": user.access_token,
                "token_type": "bearer"
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.warning(f"Session retrieval failed for user {user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid"
        )


@router.post(
    "/refresh",
    response_model=AuthResponse,
    responses={
        200: {"description": "Access token successfully refreshed"},
        401: {"model": ErrorResponse, "description": "Invalid or expired refresh token"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh an expired access token using a refresh token.
    
    When an access token expires, use this endpoint with the refresh token
    to obtain a new access token without requiring the user to log in again.
    
    Args:
        request: RefreshTokenRequest containing the refresh token
        
    Returns:
        AuthResponse: New access token, refresh token, and user information
        
    Raises:
        HTTPException: If token refresh fails (invalid or expired refresh token)
        
    Example:
        ```json
        POST /api/auth/refresh
        {
            "refresh_token": "your-refresh-token-here"
        }
        ```
    """
    try:
        logger.info("Token refresh attempt")
        
        # Use anonymous client for token refresh
        anon_client = get_anon_client()
        
        # Refresh the session using the refresh token
        response = anon_client.auth.refresh_session(request.refresh_token)
        
        if not response.user or not response.session:
            logger.warning("Token refresh failed: No user or session returned")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        logger.info(f"Token refreshed successfully for user: {response.user.id}")
        
        # Return new authentication response
        return AuthResponse(
            access_token=response.session.access_token,
            token_type="bearer",
            expires_in=response.session.expires_in or 3600,
            refresh_token=response.session.refresh_token,
            user={
                "id": response.user.id,
                "email": response.user.email,
                "created_at": response.user.created_at,
                "email_confirmed_at": response.user.email_confirmed_at
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.warning(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
