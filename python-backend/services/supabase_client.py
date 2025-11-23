"""
Supabase client initialization and management.

This module provides Supabase client instances for different use cases:
- Admin client: Uses service role key, bypasses RLS (for admin operations)
- User client factory: Creates clients with user JWT tokens (enforces RLS)
"""
from supabase import create_client, Client
from config import config
import logging

logger = logging.getLogger(__name__)

# Admin client with service role key (bypasses RLS)
# Use this for admin operations, migrations, and server-side logic
supabase_admin: Client = create_client(
    config.SUPABASE_URL,
    config.SUPABASE_SERVICE_ROLE_KEY
)

logger.info("Supabase admin client initialized")


def get_user_client(access_token: str) -> Client:
    """
    Create a Supabase client with user's JWT token for RLS enforcement.
    
    This client will respect Row Level Security policies and only allow
    access to data that the authenticated user is authorized to see.
    
    Args:
        access_token: JWT access token from Supabase Auth
        
    Returns:
        Client: Supabase client configured with user's access token
        
    Example:
        ```python
        user_client = get_user_client(user_token)
        courses = user_client.table("courses").select("*").execute()
        ```
    """
    return create_client(
        config.SUPABASE_URL,
        config.SUPABASE_ANON_KEY,
        options={
            "headers": {
                "Authorization": f"Bearer {access_token}"
            }
        }
    )


def get_anon_client() -> Client:
    """
    Create an anonymous Supabase client (no user authentication).
    
    This client uses the anon key and respects RLS policies.
    Useful for public operations like signup and public data access.
    
    Returns:
        Client: Anonymous Supabase client
    """
    return create_client(
        config.SUPABASE_URL,
        config.SUPABASE_ANON_KEY
    )
