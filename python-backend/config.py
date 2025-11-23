"""
Configuration management for FastAPI backend.
Loads and validates environment variables.
"""
import os
import sys
from typing import List
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""
    
    def __init__(self):
        """Initialize configuration and validate required variables."""
        # Gemini API Configuration
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))
        self.GEMINI_MAX_OUTPUT_TOKENS = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "1024"))
        self.GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", "30"))
        
        # Rate Limiting Configuration
        self.RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "15"))
        self.RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        
        # CORS Configuration
        allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:8080")
        self.ALLOWED_ORIGINS: List[str] = [
            origin.strip() for origin in allowed_origins_str.split(",")
        ]
        
        # Validate required configuration
        self._validate()
    
    def _validate(self):
        """
        Validate that all required configuration variables are present.
        Raises SystemExit if validation fails.
        """
        if not self.GEMINI_API_KEY:
            error_msg = (
                "FATAL ERROR: GEMINI_API_KEY environment variable is not set. "
                "Please set it in your .env file or environment variables."
            )
            logger.error(error_msg)
            print(f"\n❌ {error_msg}\n", file=sys.stderr)
            sys.exit(1)
        
        if len(self.GEMINI_API_KEY.strip()) == 0:
            error_msg = (
                "FATAL ERROR: GEMINI_API_KEY is empty. "
                "Please provide a valid API key."
            )
            logger.error(error_msg)
            print(f"\n❌ {error_msg}\n", file=sys.stderr)
            sys.exit(1)
        
        logger.info("Configuration validation successful")
        logger.info(f"Gemini Model: {self.GEMINI_MODEL}")
        logger.info(f"Rate Limit: {self.RATE_LIMIT_REQUESTS} requests per {self.RATE_LIMIT_WINDOW} seconds")
        logger.info(f"Allowed Origins: {', '.join(self.ALLOWED_ORIGINS)}")


# Global configuration instance
config = Config()
