#!/usr/bin/env python3
"""
Configuration Verification Script

This script verifies that all configuration is properly loaded and displays
the current configuration values.
"""

import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Verify configuration and display values."""
    print("=" * 70)
    print("Configuration Verification")
    print("=" * 70)
    
    try:
        # Import configuration
        from config import config
        
        print("\n✅ Configuration loaded successfully!\n")
        
        # Display configuration values
        print("Rate Limiting Configuration:")
        print(f"  - Requests per window: {config.RATE_LIMIT_REQUESTS}")
        print(f"  - Window duration: {config.RATE_LIMIT_WINDOW}s")
        
        print("\nCORS Configuration:")
        print(f"  - Allowed origins: {', '.join(config.ALLOWED_ORIGINS)}")
        
        print("\nSupabase Configuration:")
        print(f"  - URL: {config.SUPABASE_URL}")
        print(f"  - Anon key: {'*' * 20}...{config.SUPABASE_ANON_KEY[-10:]}")
        print(f"  - Service role key: {'*' * 20}...{config.SUPABASE_SERVICE_ROLE_KEY[-10:]}")
        
        print("\nAI Brain Service Configuration:")
        print(f"  - Endpoint: {config.AI_BRAIN_ENDPOINT}")
        print(f"  - Timeout: {config.AI_BRAIN_TIMEOUT}s")
        
        print("\nRetry Configuration:")
        print(f"  - Max attempts: {config.MAX_RETRY_ATTEMPTS}")
        print(f"  - Initial delay: {config.RETRY_DELAY_SECONDS}s")
        print(f"  - Backoff multiplier: {config.RETRY_BACKOFF_MULTIPLIER}x")
        
        # Calculate retry delays
        print("\n  Retry delay schedule:")
        for attempt in range(1, config.MAX_RETRY_ATTEMPTS + 1):
            delay = config.RETRY_DELAY_SECONDS * (config.RETRY_BACKOFF_MULTIPLIER ** (attempt - 1))
            print(f"    Attempt {attempt}: {delay:.1f}s")
        
        print("\n" + "=" * 70)
        print("✅ All configuration values are valid!")
        print("=" * 70)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Configuration error: {e}")
        print("\nPlease check your .env file and ensure all required variables are set.")
        print("See .env.example for reference.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
