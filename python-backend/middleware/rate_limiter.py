"""
Rate limiting middleware using slowapi.
Implements IP-based rate limiting to stay within API quotas.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# Initialize rate limiter with IP-based key function
limiter = Limiter(key_func=get_remote_address)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    Returns HTTP 429 with user-friendly message and rate limit headers.
    
    Args:
        request: The FastAPI request object
        exc: The RateLimitExceeded exception
        
    Returns:
        JSONResponse with error details and appropriate headers
    """
    # Log rate limit event
    client_ip = get_remote_address(request)
    logger.warning(f"Rate limit exceeded for IP: {client_ip}")
    
    # Import config to get rate limit values
    from config import config
    
    response = JSONResponse(
        status_code=429,
        content={
            "error": "You've reached the message limit. Please try again in a moment.",
            "code": "RATE_LIMIT_EXCEEDED"
        }
    )
    
    # Add rate limit headers
    response.headers["Retry-After"] = str(config.RATE_LIMIT_WINDOW)
    response.headers["X-RateLimit-Limit"] = str(config.RATE_LIMIT_REQUESTS)
    response.headers["X-RateLimit-Remaining"] = "0"
    
    return response
