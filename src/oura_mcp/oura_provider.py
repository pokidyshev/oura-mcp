"""Oura OAuth Provider for FastMCP."""

from typing import Optional
import httpx

from fastmcp.server.auth import OAuthProxy
from fastmcp.server.dependencies import AccessToken


class OuraTokenVerifier:
    """
    Token verifier for Oura's opaque OAuth tokens.

    Validates tokens by making API calls to Oura's API, similar to how
    GitHubProvider validates GitHub tokens.
    """

    def __init__(self):
        """Initialize the Oura token verifier."""
        self.required_scopes = [
            "email",
            "personal",
            "daily",
            "heartrate",
            "workout",
            "session",
            "tag",
            "spo2Daily",
        ]

    def verify_token(self, token: str) -> Optional[AccessToken]:
        """
        Verify an Oura access token by calling Oura's API.

        Args:
            token: The Oura access token to verify

        Returns:
            AccessToken if valid, None otherwise
        """
        try:
            # Call Oura's personal_info endpoint to validate token
            with httpx.Client() as client:
                response = client.get(
                    "https://api.ouraring.com/v2/usercollection/personal_info",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    user_id = data.get("id", "unknown")
                    email = data.get("email")

                    # Create AccessToken with user info in claims
                    return AccessToken(
                        token=token,
                        client_id=user_id,
                        scopes=self.required_scopes,
                        claims={
                            "sub": user_id,
                            "email": email,
                        },
                    )

                # Invalid token
                return None

        except Exception:
            # Network error or invalid response
            return None


class OuraProvider(OAuthProxy):
    """
    OAuth provider for Oura Ring API.

    Extends OAuthProxy to work with Oura's OAuth system, which doesn't
    support Dynamic Client Registration (DCR). Similar to GitHubProvider,
    this bridges the gap between MCP's DCR expectations and Oura's manual
    app registration requirement.

    Example:
        ```python
        from oura_mcp.oura_provider import OuraProvider

        auth = OuraProvider(
            client_id="your-oura-client-id",
            client_secret="your-oura-client-secret",
            base_url="https://your-server.com"
        )

        mcp = FastMCP("My Server", auth=auth)
        ```
    """

    def __init__(self, client_id: str, client_secret: str, base_url: str, **kwargs):
        """
        Initialize Oura OAuth provider.

        Args:
            client_id: Your Oura OAuth application client ID
            client_secret: Your Oura OAuth application client secret
            base_url: Your FastMCP server's public URL (e.g., https://your-app.fastmcp.app)
            **kwargs: Additional arguments passed to OAuthProxy
        """
        # Create Oura-specific token verifier
        token_verifier = OuraTokenVerifier()

        # Initialize OAuthProxy with Oura endpoints
        super().__init__(
            upstream_authorization_endpoint="https://cloud.ouraring.com/oauth/authorize",
            upstream_token_endpoint="https://api.ouraring.com/oauth/token",
            upstream_client_id=client_id,
            upstream_client_secret=client_secret,
            base_url=base_url,
            token_verifier=token_verifier,
            redirect_path="/mcp/auth/callback",
            # Oura scopes
            extra_authorize_params={
                "scope": "email personal daily heartrate workout session tag spo2Daily"
            },
            **kwargs,
        )
