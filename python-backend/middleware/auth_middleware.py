"""
Authentication middleware for FastAPI.

This middleware extracts and validates JWT tokens from the Authorization header
and attaches user information to the request state for downstream use.
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging

from services.auth_service import verify_jwt_token

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and validate JWT tokens from Authorization header.
    
    This middleware:
    1. Extracts the Bearer token from the Authorization header
    2. Validates the token using Supabase Auth
    3. Attaches user info to request.state for downstream access
    4. Allows unauthenticated requests to pass through (auth enforcement is per-route)
    
    The middleware does NOT block unauthenticated requests - it only enriches
    the request with user information if a valid token is provided. Route-level
    authentication should be enforced using the get_current_user dependency.
    
    Usage:
        ```python
        from middleware.auth_middleware import AuthMiddleware
        
        app = FastAPI()
        app.add_middleware(AuthMiddleware)
        
        @app.get("/api/profile")
        async def get_profile(request: Request):
            # Access user info from request state
            if hasattr(request.state, 'user'):
                user = request.state.user
                return {"user_id": user["id"], "email": user["email"]}
            else:
                return {"message": "Not authenticated"}
        ```
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process the request and attach user info if authenticated.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            Response from the next handler
        """
        # Initialize user state as None
        request.state.user = None
        request.state.access_token = None
        
        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        
        if auth_header:
            # Check if it's a Bearer token
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]  # Remove "Bearer " prefix
                
                try:
                    # Verify the token and get user data
                    user_data = await verify_jwt_token(token)
                    
                    if user_data:
                        # Attach user info to request state
                        request.state.user = user_data
                        request.state.access_token = token
                        logger.debug(f"Request authenticated for user: {user_data['id']}")
                    else:
                        logger.debug("Token verification returned no user data")
                        
                except HTTPException as e:
                    # Token is invalid or expired
                    # Log but don't block the request - let route handlers decide
                    logger.debug(f"Invalid token in request: {e.detail}")
                    
                except Exception as e:
                    # Unexpected error during token verification
                    logger.error(f"Error processing auth token: {str(e)}")
            else:
                logger.debug("Authorization header present but not Bearer token")
        
        # Continue processing the request
        response = await call_next(request)
        return response


class RequireAuthMiddleware(BaseHTTPMiddleware):
    """
    Strict authentication middleware that blocks all unauthenticated requests.
    
    This middleware is more restrictive than AuthMiddleware - it requires
    a valid JWT token for ALL requests and returns 401 for unauthenticated requests.
    
    Use this middleware when you want to protect an entire API or router,
    rather than individual routes.
    
    Usage:
        ```python
        from middleware.auth_middleware import RequireAuthMiddleware
        
        # Protect entire API
        app = FastAPI()
        app.add_middleware(RequireAuthMiddleware)
        
        # Or protect specific router
        protected_router = APIRouter()
        protected_router.add_middleware(RequireAuthMiddleware)
        ```
    """
    
    # Routes that don't require authentication
    PUBLIC_PATHS = [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/auth/signup",
        "/api/auth/login",
        "/api/auth/refresh",
    ]
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process the request and require authentication.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            Response from the next handler or 401 error
        """
        # Check if path is public
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)
        
        # Initialize user state
        request.state.user = None
        request.state.access_token = None
        
        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            logger.warning(f"Unauthenticated request to protected path: {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if it's a Bearer token
        if not auth_header.startswith("Bearer "):
            logger.warning(f"Invalid Authorization header format: {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication header format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            # Verify the token and get user data
            user_data = await verify_jwt_token(token)
            
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Attach user info to request state
            request.state.user = user_data
            request.state.access_token = token
            logger.debug(f"Authenticated request for user: {user_data['id']}")
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
            
        except Exception as e:
            # Unexpected error during token verification
            logger.error(f"Error processing auth token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Continue processing the request
        response = await call_next(request)
        return response
