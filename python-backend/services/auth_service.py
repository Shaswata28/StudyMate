"""
Authentication service for Supabase JWT token verification and user management.

This module provides utilities for:
- Verifying JWT tokens from Supabase Auth
- Extracting user information from JWT tokens
- FastAPI dependencies for protected routes
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from services.supabase_client import supabase_admin, get_user_client

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer()


class AuthUser:
    """
    Represents an authenticated user extracted from JWT token.
    
    Attributes:
        id: User's UUID from Supabase Auth
        email: User's email address
        access_token: JWT access token for making authenticated requests
    """
    def __init__(self, id: str, email: str, access_token: str):
        self.id = id
        self.email = email
        self.access_token = access_token
    
    def __repr__(self):
        return f"AuthUser(id={self.id}, email={self.email})"


async def verify_jwt_token(token: str) -> Optional[dict]:
    """
    Verify a JWT token using Supabase Auth.
    
    This function validates the token signature, expiration, and other claims
    using Supabase's built-in verification.
    
    Args:
        token: JWT access token to verify
        
    Returns:
        dict: User data from the token if valid, None if invalid
        
    Raises:
        HTTPException: If token is invalid or expired
        
    Example:
        ```python
        user_data = await verify_jwt_token(access_token)
        print(f"User ID: {user_data['id']}")
        ```
    """
    try:
        # Use Supabase admin client to verify the JWT token
        # This validates the token signature and expiration
        user_response = supabase_admin.auth.get_user(token)
        
        if user_response and user_response.user:
            logger.debug(f"Token verified for user: {user_response.user.id}")
            return {
                "id": user_response.user.id,
                "email": user_response.user.email,
                "role": user_response.user.role if hasattr(user_response.user, 'role') else 'authenticated'
            }
        else:
            logger.warning("Token verification failed: No user data returned")
            return None
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.warning(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_user_from_token(token: str) -> AuthUser:
    """
    Extract user information from a JWT token.
    
    This function verifies the token and returns an AuthUser object
    containing the user's ID, email, and access token.
    
    Args:
        token: JWT access token
        
    Returns:
        AuthUser: Authenticated user object
        
    Raises:
        HTTPException: If token is invalid or expired
        
    Example:
        ```python
        user = await get_user_from_token(access_token)
        print(f"Authenticated as: {user.email}")
        ```
    """
    user_data = await verify_jwt_token(token)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return AuthUser(
        id=user_data["id"],
        email=user_data["email"],
        access_token=token
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> AuthUser:
    """
    FastAPI dependency for protected routes that require authentication.
    
    This dependency extracts the JWT token from the Authorization header,
    verifies it, and returns the authenticated user. If the token is missing,
    invalid, or expired, it raises an HTTP 401 Unauthorized exception.
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        
    Returns:
        AuthUser: Authenticated user object
        
    Raises:
        HTTPException: If authentication fails
        
    Usage:
        ```python
        @router.get("/protected")
        async def protected_route(user: AuthUser = Depends(get_current_user)):
            return {"message": f"Hello {user.email}"}
        ```
    """
    if not credentials or not credentials.credentials:
        logger.warning("No credentials provided in Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    user = await get_user_from_token(token)
    
    logger.info(f"User authenticated: {user.id}")
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[AuthUser]:
    """
    FastAPI dependency for routes that optionally support authentication.
    
    This dependency is similar to get_current_user but doesn't raise an error
    if no token is provided. It returns None for unauthenticated requests.
    
    Args:
        credentials: Optional HTTP Bearer credentials from Authorization header
        
    Returns:
        AuthUser: Authenticated user object if token provided, None otherwise
        
    Usage:
        ```python
        @router.get("/public-or-private")
        async def flexible_route(user: Optional[AuthUser] = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello {user.email}"}
            else:
                return {"message": "Hello anonymous user"}
        ```
    """
    if not credentials or not credentials.credentials:
        return None
    
    try:
        token = credentials.credentials
        user = await get_user_from_token(token)
        logger.info(f"Optional auth: User authenticated: {user.id}")
        return user
    except HTTPException:
        # If token is invalid, return None instead of raising error
        logger.debug("Optional auth: Invalid token provided, treating as anonymous")
        return None
