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
        # Rate Limiting Configuration
        self.RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "15"))
        self.RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        
        # CORS Configuration
        allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:8080")
        self.ALLOWED_ORIGINS: List[str] = [
            origin.strip() for origin in allowed_origins_str.split(",")
        ]
        
        # Supabase Configuration
        self.SUPABASE_URL = os.getenv("SUPABASE_URL")
        self.SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
        self.SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        # Validate required configuration
        self._validate()
    
    def _validate(self):
        """
        Validate that all required configuration variables are present.
        Raises SystemExit if validation fails.
        """
        errors = []
        
        # Validate Supabase Configuration
        if not self.SUPABASE_URL:
            errors.append("SUPABASE_URL environment variable is not set")
        elif not self.SUPABASE_URL.startswith("https://"):
            errors.append("SUPABASE_URL must start with https://")
        
        if not self.SUPABASE_ANON_KEY:
            errors.append("SUPABASE_ANON_KEY environment variable is not set")
        elif len(self.SUPABASE_ANON_KEY.strip()) == 0:
            errors.append("SUPABASE_ANON_KEY is empty")
        
        if not self.SUPABASE_SERVICE_ROLE_KEY:
            errors.append("SUPABASE_SERVICE_ROLE_KEY environment variable is not set")
        elif len(self.SUPABASE_SERVICE_ROLE_KEY.strip()) == 0:
            errors.append("SUPABASE_SERVICE_ROLE_KEY is empty")
        
        # If there are errors, log and exit
        if errors:
            error_msg = "FATAL ERROR: Configuration validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
            logger.error(error_msg)
            print(f"\n❌ {error_msg}\n", file=sys.stderr)
            print("Please check your .env file and ensure all required variables are set.\n", file=sys.stderr)
            sys.exit(1)
        
        logger.info("Configuration validation successful")
        logger.info(f"Rate Limit: {self.RATE_LIMIT_REQUESTS} requests per {self.RATE_LIMIT_WINDOW} seconds")
        logger.info(f"Allowed Origins: {', '.join(self.ALLOWED_ORIGINS)}")
        logger.info(f"Supabase URL: {self.SUPABASE_URL}")


# Global configuration instance
config = Config()
