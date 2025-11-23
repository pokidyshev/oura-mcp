"""Configuration management for Oura MCP Server."""

import json
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class OuraConfig:
    """Configuration for Oura API authentication and token management.

    Supports two authentication methods:
    1. Personal Access Token (PAT) - Simple, recommended for personal use
       - Only requires OURA_ACCESS_TOKEN
       - ✅ TESTED
    2. OAuth2 with refresh tokens - Advanced, for production applications
       - Requires OURA_ACCESS_TOKEN, OURA_REFRESH_TOKEN, OURA_CLIENT_ID, OURA_CLIENT_SECRET
       - ⚠️  WARNING: NOT TESTED YET!
    """

    def __init__(self):
        """Initialize configuration from environment variables and token file."""
        # OAuth2 credentials (optional, only needed for token refresh)
        self.client_id = os.getenv("OURA_CLIENT_ID")
        self.client_secret = os.getenv("OURA_CLIENT_SECRET")

        # Token file for persistence (LOCAL/DEV/TESTING ONLY - not for production)
        self.token_file = Path(os.getenv("OURA_TOKEN_FILE", ".oura_tokens.json"))

        # Load tokens from file if it exists, otherwise from environment
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

        self._load_tokens()

    def _load_tokens(self) -> None:
        """Load tokens from file or environment variables."""
        # Try to load from token file first
        if self.token_file.exists():
            try:
                with open(self.token_file, "r") as f:
                    tokens = json.load(f)
                    self.access_token = tokens.get("access_token")
                    self.refresh_token = tokens.get("refresh_token")
                    return
            except (json.JSONDecodeError, IOError):
                pass  # Fall through to environment variables

        # Fall back to environment variables
        self.access_token = os.getenv("OURA_ACCESS_TOKEN")
        self.refresh_token = os.getenv("OURA_REFRESH_TOKEN")

    def save_tokens(self, access_token: str, refresh_token: str) -> None:
        """
        Save tokens to file for persistence (LOCAL/DEV/TESTING ONLY).

        Args:
            access_token: New access token
            refresh_token: New refresh token
        """
        self.access_token = access_token
        self.refresh_token = refresh_token

        try:
            with open(self.token_file, "w") as f:
                json.dump(
                    {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                    },
                    f,
                    indent=2,
                )
        except IOError as e:
            # Log error but don't crash - tokens are still in memory
            print(f"Warning: Could not save tokens to {self.token_file}: {e}")

    def validate(self) -> tuple[bool, str]:
        """
        Validate that required configuration is present.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.access_token:
            return False, (
                "OURA_ACCESS_TOKEN is required but not set.\n"
                "Get your Personal Access Token from: https://cloud.ouraring.com/personal-access-tokens"
            )

        # If OAuth2 refresh is configured, validate all required components
        if self.refresh_token and not (self.client_id and self.client_secret):
            return (
                False,
                "OURA_CLIENT_ID and OURA_CLIENT_SECRET are required when using OURA_REFRESH_TOKEN",
            )

        return True, ""

    def is_using_oauth2(self) -> bool:
        """Check if OAuth2 with refresh tokens is configured."""
        return bool(self.refresh_token and self.client_id and self.client_secret)


# Global configuration instance
config = OuraConfig()
