"""
Example router demonstrating authentication usage.

This file shows how to use the authentication utilities in your routes.
You can use this as a reference when building authenticated endpoints.
"""
from fastapi import APIRouter, Depends, Request
from typing import Optional

from services.auth_service import get_current_user, get_current_user_optional, AuthUser

router = APIRouter(prefix="/api/examples", tags=["examples"])


@router.get("/public")
async def public_route():
    """
    Public route - no authentication required.
    
    Anyone can access this endpoint without a token.
    """
    return {
        "message": "This is a public endpoint",
        "authentication": "not required"
    }


@router.get("/protected")
async def protected_route(user: AuthUser = Depends(get_current_user)):
    """
    Protected route - authentication required.
    
    This endpoint requires a valid JWT token in the Authorization header.
    If no token or an invalid token is provided, returns 401 Unauthorized.
    
    Headers:
        Authorization: Bearer <jwt_token>
    """
    return {
        "message": f"Hello {user.email}!",
        "user_id": user.id,
        "authentication": "required"
    }


@router.get("/optional-auth")
async def optional_auth_route(user: Optional[AuthUser] = Depends(get_current_user_optional)):
    """
    Optional authentication route.
    
    This endpoint works with or without authentication.
    If a valid token is provided, returns personalized response.
    If no token or invalid token, returns generic response.
    """
    if user:
        return {
            "message": f"Welcome back, {user.email}!",
            "user_id": user.id,
            "authenticated": True
        }
    else:
        return {
            "message": "Welcome, guest!",
            "authenticated": False
        }


@router.get("/user-info")
async def get_user_info(user: AuthUser = Depends(get_current_user)):
    """
    Get detailed information about the authenticated user.
    
    This demonstrates accessing user properties from the AuthUser object.
    """
    return {
        "user": {
            "id": user.id,
            "email": user.email,
        },
        "token_info": {
            "has_access_token": bool(user.access_token),
            "token_length": len(user.access_token) if user.access_token else 0
        }
    }


@router.get("/middleware-example")
async def middleware_example(request: Request):
    """
    Example of accessing user info from request.state (set by AuthMiddleware).
    
    This approach is useful when you want to check authentication status
    without using the dependency injection pattern.
    
    Note: This requires AuthMiddleware to be registered in main.py
    """
    if hasattr(request.state, 'user') and request.state.user:
        user = request.state.user
        return {
            "message": "User info from middleware",
            "user_id": user["id"],
            "email": user["email"],
            "source": "request.state (middleware)"
        }
    else:
        return {
            "message": "No authentication info in request state",
            "note": "Make sure AuthMiddleware is registered in main.py"
        }
