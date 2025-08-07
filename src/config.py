import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def get_env_var(key: str, default: str = None) -> str:
    """Get environment variable with optional default value."""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Environment variable '{key}' is required but not set")
    return value

# Database Configuration
DATABASE_CONFIG = {
    "connection_string": f"""
        DRIVER={{{get_env_var('DB_DRIVER')}}};
        SERVER={get_env_var('DB_SERVER')};
        DATABASE={get_env_var('DB_NAME')};
        UID={get_env_var('DB_USER')};
        PWD={get_env_var('DB_PASSWORD')};
        TrustServerCertificate=yes;""",
    "trade_connection_string": f"""
        DRIVER={{{get_env_var('DB_DRIVER')}}};
        SERVER={get_env_var('DB_SERVER')};
        DATABASE={get_env_var('DB_TRADE_NAME')};
        UID={get_env_var('DB_USER')};
        PWD={get_env_var('DB_PASSWORD')};
        TrustServerCertificate=yes;""",
}

# Email Configuration
EMAIL_CONFIG = {
    "mail": get_env_var('EMAIL_ADDRESS'), 
    "password": get_env_var('EMAIL_PASSWORD')
}

# Turnstile Configuration
TURNSTILE_PRIVATE_KEY = get_env_var('TURNSTILE_PRIVATE_KEY')
TURNSTILE_ENDPOINT = get_env_var('TURNSTILE_ENDPOINT', 'https://challenges.cloudflare.com/turnstile/v0/siteverify')

# CORS Configuration
def get_cors_origins():
    """Parse CORS origins from environment variable."""
    cors_origins = get_env_var('CORS_ORIGINS', '*')
    if cors_origins == '*':
        return ["*"]
    # Split by comma and strip whitespace
    return [origin.strip() for origin in cors_origins.split(',') if origin.strip()]

CORS_ORIGINS = get_cors_origins()
