"""
Logging middleware for FastAPI application.
Logs all incoming requests with metadata including timestamp, endpoint, IP, status, and duration.
"""
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests with comprehensive metadata.
    Logs: timestamp, endpoint, method, IP address, status code, and request duration.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and log metadata.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            The HTTP response
        """
        # Record start time
        start_time = time.time()
        
        # Get client IP address
        client_ip = request.client.host if request.client else "unknown"
        
        # Log incoming request
        logger.info(
            f"Incoming request - Method: {request.method}, "
            f"Path: {request.url.path}, "
            f"IP: {client_ip}"
        )
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            logger.info(
                f"Request completed - Method: {request.method}, "
                f"Path: {request.url.path}, "
                f"Status: {response.status_code}, "
                f"Duration: {duration_ms:.2f}ms, "
                f"IP: {client_ip}"
            )
            
            return response
            
        except Exception as e:
            # Calculate duration even for errors
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error with full details
            logger.error(
                f"Request failed - Method: {request.method}, "
                f"Path: {request.url.path}, "
                f"Duration: {duration_ms:.2f}ms, "
                f"IP: {client_ip}, "
                f"Error: {type(e).__name__}: {str(e)}",
                exc_info=True
            )
            
            # Re-raise the exception to be handled by FastAPI
            raise
