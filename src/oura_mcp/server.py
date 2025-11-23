"""Oura MCP Server - Main server implementation."""

import json
import os
from datetime import datetime, timedelta
from typing import Optional

from fastmcp import FastMCP

from oura_mcp.config import config
from oura_mcp.oura_client import OuraClient, OuraAPIError
from oura_mcp.oura_provider import OuraProvider

# OAuth2 Configuration for Oura
# These should be set in your FastMCP Cloud environment
CLIENT_ID = os.getenv("OURA_CLIENT_ID")
CLIENT_SECRET = os.getenv("OURA_CLIENT_SECRET")
# The full URL where your server is deployed
DEPLOYED_URL = os.getenv("DEPLOYED_URL", "https://oura-mcp.fastmcp.app")

# Configure Oura OAuth Provider (only if credentials are provided)
# OuraProvider extends OAuthProxy with Oura-specific token validation
auth = None
if CLIENT_ID and CLIENT_SECRET:
    auth = OuraProvider(
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET, base_url=DEPLOYED_URL
    )

# Initialize FastMCP server with OAuth (if configured) or without auth (for local PAT usage)
# FastMCP Cloud requires listening on 0.0.0.0
mcp = FastMCP("Oura Ring Health Data Server", auth=auth, host="0.0.0.0", port=8080)


def get_oura_client() -> OuraClient:
    """
    Get an OuraClient instance with the appropriate access token.

    In OAuth mode (production), attempts to get the upstream Oura token.
    In PAT mode (local dev), uses the token from environment/config.

    Note: OAuthProxy stores upstream tokens internally. For production use,
    the upstream token needs to be accessed via the auth provider's storage.
    This implementation tries to get it from the access token claims where
    the upstream token may be stored.
    """
    try:
        # Try to get access token from FastMCP
        from fastmcp.server.dependencies import get_access_token

        token = get_access_token()
        if token:
            # Check if the upstream token is in claims
            # OAuthProxy may store it in token claims or we need custom storage access
            upstream_token = token.claims.get("upstream_access_token")
            if upstream_token:
                return OuraClient(access_token=upstream_token)

            # If no upstream token in claims, the token string itself might be usable
            # This depends on how OAuthProxy is configured
            if hasattr(token, "token"):
                return OuraClient(access_token=token.token)
    except (ImportError, RuntimeError, AttributeError):
        # Context not available or not in OAuth mode
        pass

    # Fall back to config-based token (for local PAT usage)
    return OuraClient()


def parse_date(date_str: Optional[str]) -> str:
    """
    Parse date string, supporting natural language.

    Args:
        date_str: Date in YYYY-MM-DD format or natural language (today, yesterday, etc.)

    Returns:
        Date string in YYYY-MM-DD format
    """
    if not date_str:
        return datetime.now().strftime("%Y-%m-%d")

    date_str = date_str.lower().strip()

    if date_str == "today":
        return datetime.now().strftime("%Y-%m-%d")
    elif date_str == "yesterday":
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    elif date_str.startswith("last week"):
        return (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    elif date_str.startswith("last month"):
        return (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    # Assume it's already in YYYY-MM-DD format
    return date_str


def format_response(data: any) -> str:
    """Format API response as pretty JSON."""
    return json.dumps(data, indent=2, default=str)


# ============================================================================
# TOOLS - Interactive data fetching with parameters
# ============================================================================


# Core Daily Summaries
@mcp.tool()
def get_daily_sleep(
    start_date: str = "last week", end_date: Optional[str] = None
) -> str:
    """
    Get daily sleep summaries including sleep score and contributors.

    Args:
        start_date: Start date (YYYY-MM-DD or 'today', 'yesterday', 'last week')
        end_date: End date (YYYY-MM-DD, optional)

    Returns:
        JSON array of daily sleep summaries with scores and contributors
    """
    try:
        client = get_oura_client()
        start = parse_date(start_date)
        end = parse_date(end_date) if end_date else None
        data = client.get_daily_sleep(start, end)
        return format_response(data)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_daily_activity(
    start_date: str = "last week", end_date: Optional[str] = None
) -> str:
    """
    Get daily activity summaries including activity score, steps, and calories.

    Args:
        start_date: Start date (YYYY-MM-DD or 'today', 'yesterday', 'last week')
        end_date: End date (YYYY-MM-DD, optional)

    Returns:
        JSON array of daily activity summaries with scores, steps, calories, and MET data
    """
    try:
        client = get_oura_client()
        start = parse_date(start_date)
        end = parse_date(end_date) if end_date else None
        data = client.get_daily_activity(start, end)
        return format_response(data)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_daily_readiness(
    start_date: str = "last week", end_date: Optional[str] = None
) -> str:
    """
    Get daily readiness summaries including readiness score and contributors.

    Args:
        start_date: Start date (YYYY-MM-DD or 'today', 'yesterday', 'last week')
        end_date: End date (YYYY-MM-DD, optional)

    Returns:
        JSON array of readiness scores with contributors (HRV, temperature, sleep balance, etc.)
    """
    try:
        client = get_oura_client()
        start = parse_date(start_date)
        end = parse_date(end_date) if end_date else None
        data = client.get_daily_readiness(start, end)
        return format_response(data)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_daily_stress(
    start_date: str = "last week", end_date: Optional[str] = None
) -> str:
    """
    Get daily stress summaries including stress and recovery time.

    Args:
        start_date: Start date (YYYY-MM-DD or 'today', 'yesterday', 'last week')
        end_date: End date (YYYY-MM-DD, optional)

    Returns:
        JSON array with stress_high and recovery_high seconds, plus day_summary
    """
    try:
        client = get_oura_client()
        start = parse_date(start_date)
        end = parse_date(end_date) if end_date else None
        data = client.get_daily_stress(start, end)
        return format_response(data)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


# Detailed Sleep Data
@mcp.tool()
def get_sleep_periods(
    start_date: str = "last week", end_date: Optional[str] = None
) -> str:
    """
    Get detailed sleep periods with phases, heart rate, HRV, and breathing data.

    Args:
        start_date: Start date (YYYY-MM-DD or 'today', 'yesterday', 'last week')
        end_date: End date (YYYY-MM-DD, optional)

    Returns:
        JSON array of detailed sleep sessions including sleep phases, biometrics, and efficiency
    """
    try:
        start = parse_date(start_date)
        end = parse_date(end_date) if end_date else None
        client = get_oura_client()
        data = client.get_sleep_periods(start, end)
        return format_response(data)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_sleep_time(
    start_date: str = "last week", end_date: Optional[str] = None
) -> str:
    """
    Get optimal bedtime recommendations.

    Args:
        start_date: Start date (YYYY-MM-DD or 'today', 'yesterday', 'last week')
        end_date: End date (YYYY-MM-DD, optional)

    Returns:
        JSON array of optimal bedtime recommendations with status and actions
    """
    try:
        start = parse_date(start_date)
        end = parse_date(end_date) if end_date else None
        client = get_oura_client()
        data = client.get_sleep_time(start, end)
        return format_response(data)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


# Activity & Workouts
@mcp.tool()
def get_workouts(start_date: str = "last week", end_date: Optional[str] = None) -> str:
    """
    Get workout summaries including activity type, intensity, calories, and distance.

    Args:
        start_date: Start date (YYYY-MM-DD or 'today', 'yesterday', 'last week')
        end_date: End date (YYYY-MM-DD, optional)

    Returns:
        JSON array of workout summaries with type, intensity, duration, and metrics
    """
    try:
        start = parse_date(start_date)
        end = parse_date(end_date) if end_date else None
        client = get_oura_client()
        data = client.get_workouts(start, end)
        return format_response(data)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_sessions(start_date: str = "last week", end_date: Optional[str] = None) -> str:
    """
    Get session data (meditation, breathing exercises, naps, etc.).

    Args:
        start_date: Start date (YYYY-MM-DD or 'today', 'yesterday', 'last week')
        end_date: End date (YYYY-MM-DD, optional)

    Returns:
        JSON array of sessions with type, heart rate, HRV, and mood data
    """
    try:
        start = parse_date(start_date)
        end = parse_date(end_date) if end_date else None
        client = get_oura_client()
        data = client.get_sessions(start, end)
        return format_response(data)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


# Time-Series Data
@mcp.tool()
def get_heartrate(start_datetime: str, end_datetime: Optional[str] = None) -> str:
    """
    Get heart rate time-series data in 5-minute intervals.

    Args:
        start_datetime: Start datetime in ISO 8601 format (e.g., 2023-01-01T00:00:00-08:00)
        end_datetime: End datetime in ISO 8601 format (optional)

    Returns:
        JSON array of heart rate measurements with BPM, source, and timestamp
    """
    try:
        client = get_oura_client()
        data = client.get_heartrate(start_datetime, end_datetime)
        return format_response(data)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


# Advanced Metrics
@mcp.tool()
def get_daily_spo2(
    start_date: str = "last week", end_date: Optional[str] = None
) -> str:
    """
    Get daily SpO2 (blood oxygen) averages during sleep (Gen 3 ring only).

    Args:
        start_date: Start date (YYYY-MM-DD or 'today', 'yesterday', 'last week')
        end_date: End date (YYYY-MM-DD, optional)

    Returns:
        JSON array of SpO2 percentages and breathing disturbance index
    """
    try:
        start = parse_date(start_date)
        end = parse_date(end_date) if end_date else None
        client = get_oura_client()
        data = client.get_daily_spo2(start, end)
        return format_response(data)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_vo2_max(start_date: str = "last week", end_date: Optional[str] = None) -> str:
    """
    Get VO2 max estimates (cardiorespiratory fitness indicator).

    Args:
        start_date: Start date (YYYY-MM-DD or 'today', 'yesterday', 'last week')
        end_date: End date (YYYY-MM-DD, optional)

    Returns:
        JSON array of VO2 max estimates with day and timestamp
    """
    try:
        start = parse_date(start_date)
        end = parse_date(end_date) if end_date else None
        client = get_oura_client()
        data = client.get_vo2_max(start, end)
        return format_response(data)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_daily_resilience(
    start_date: str = "last week", end_date: Optional[str] = None
) -> str:
    """
    Get daily resilience scores and levels.

    Args:
        start_date: Start date (YYYY-MM-DD or 'today', 'yesterday', 'last week')
        end_date: End date (YYYY-MM-DD, optional)

    Returns:
        JSON array with resilience level (limited/adequate/solid/strong/exceptional) and contributors
    """
    try:
        start = parse_date(start_date)
        end = parse_date(end_date) if end_date else None
        client = get_oura_client()
        data = client.get_daily_resilience(start, end)
        return format_response(data)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_cardiovascular_age(
    start_date: str = "last week", end_date: Optional[str] = None
) -> str:
    """
    Get predicted cardiovascular age (vascular age prediction).

    Args:
        start_date: Start date (YYYY-MM-DD or 'today', 'yesterday', 'last week')
        end_date: End date (YYYY-MM-DD, optional)

    Returns:
        JSON array with predicted vascular age [18-100]
    """
    try:
        start = parse_date(start_date)
        end = parse_date(end_date) if end_date else None
        client = get_oura_client()
        data = client.get_daily_cardiovascular_age(start, end)
        return format_response(data)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


# User Data
@mcp.tool()
def get_personal_info() -> str:
    """
    Get user's personal information (age, weight, height, biological sex, email).

    Returns:
        JSON object with personal information and user ID
    """
    try:
        client = get_oura_client()
        data = client.get_personal_info()
        return format_response(data)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_ring_configuration() -> str:
    """
    Get Oura Ring device information (model, color, size, firmware version).

    Returns:
        JSON array with ring configuration details including hardware type and setup date
    """
    try:
        client = get_oura_client()
        data = client.get_ring_configuration()
        return format_response(data)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_enhanced_tags(
    start_date: str = "last week", end_date: Optional[str] = None
) -> str:
    """
    Get user-entered tags and annotations.

    Args:
        start_date: Start date (YYYY-MM-DD or 'today', 'yesterday', 'last week')
        end_date: End date (YYYY-MM-DD, optional)

    Returns:
        JSON array of tags with tag_type_code, custom_name, time range, and comments
    """
    try:
        start = parse_date(start_date)
        end = parse_date(end_date) if end_date else None
        client = get_oura_client()
        data = client.get_enhanced_tags(start, end)
        return format_response(data)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_rest_mode_periods(
    start_date: str = "last week", end_date: Optional[str] = None
) -> str:
    """
    Get rest mode periods (when user has enabled rest mode).

    Args:
        start_date: Start date (YYYY-MM-DD or 'today', 'yesterday', 'last week')
        end_date: End date (YYYY-MM-DD, optional)

    Returns:
        JSON array of rest mode periods with start/end dates and episodes
    """
    try:
        start = parse_date(start_date)
        end = parse_date(end_date) if end_date else None
        client = get_oura_client()
        data = client.get_rest_mode_periods(start, end)
        return format_response(data)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


# ============================================================================
# RESOURCES - Quick access to recent summaries (no parameters)
# ============================================================================


@mcp.resource("oura://summary/today")
def get_today_summary() -> str:
    """Today's readiness, sleep, and activity scores."""
    try:
        client = get_oura_client()
        today = datetime.now().strftime("%Y-%m-%d")

        readiness_data = client.get_daily_readiness(today, today)
        sleep_data = client.get_daily_sleep(today, today)
        activity_data = client.get_daily_activity(today, today)

        summary = {
            "date": today,
            "readiness": readiness_data[0] if readiness_data else None,
            "sleep": sleep_data[0] if sleep_data else None,
            "activity": activity_data[0] if activity_data else None,
        }

        return format_response(summary)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


@mcp.resource("oura://summary/yesterday")
def get_yesterday_summary() -> str:
    """Yesterday's readiness, sleep, and activity scores."""
    try:
        client = get_oura_client()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        readiness_data = client.get_daily_readiness(yesterday, yesterday)
        sleep_data = client.get_daily_sleep(yesterday, yesterday)
        activity_data = client.get_daily_activity(yesterday, yesterday)

        summary = {
            "date": yesterday,
            "readiness": readiness_data[0] if readiness_data else None,
            "sleep": sleep_data[0] if sleep_data else None,
            "activity": activity_data[0] if activity_data else None,
        }

        return format_response(summary)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


@mcp.resource("oura://personal/info")
def get_personal_info_resource() -> str:
    """Personal information and ring configuration."""
    try:
        client = get_oura_client()
        personal = client.get_personal_info()
        ring = client.get_ring_configuration()

        info = {
            "personal_info": personal,
            "ring_configuration": ring[0] if ring else None,
        }

        return format_response(info)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


@mcp.resource("oura://recent/sleep")
def get_recent_sleep() -> str:
    """Last 7 days of sleep scores."""
    try:
        start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        end = datetime.now().strftime("%Y-%m-%d")

        client = get_oura_client()
        data = client.get_daily_sleep(start, end)
        return format_response(data)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


@mcp.resource("oura://recent/activity")
def get_recent_activity() -> str:
    """Last 7 days of activity scores."""
    try:
        start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        end = datetime.now().strftime("%Y-%m-%d")

        client = get_oura_client()
        data = client.get_daily_activity(start, end)
        return format_response(data)
    except OuraAPIError as e:
        return format_response({"error": str(e), "status_code": e.status_code})


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main():
    """Main entry point for the MCP server."""
    # Validate configuration
    is_valid, error_msg = config.validate()
    if not is_valid:
        print(f"❌ Configuration error: {error_msg}")
        print("\n" + "=" * 60)
        print("QUICK START - Personal Access Token (Recommended)")
        print("=" * 60)
        print("1. Go to: https://cloud.ouraring.com/personal-access-tokens")
        print("2. Create a new Personal Access Token")
        print("3. Set environment variable: OURA_ACCESS_TOKEN=your_token_here")
        print("\nFor .env file setup:")
        print("  cp .env.example .env")
        print("  # Edit .env and add your OURA_ACCESS_TOKEN")
        print("\n" + "=" * 60)
        print("ADVANCED - OAuth2 with Automatic Token Refresh")
        print("=" * 60)
        print("For production apps, set all of these:")
        print("  - OURA_ACCESS_TOKEN")
        print("  - OURA_REFRESH_TOKEN")
        print("  - OURA_CLIENT_ID")
        print("  - OURA_CLIENT_SECRET")
        return

    # Show authentication mode
    if config.is_using_oauth2():
        print("✅ Using OAuth2 with automatic token refresh")
    else:
        print("✅ Using Personal Access Token")

    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()
