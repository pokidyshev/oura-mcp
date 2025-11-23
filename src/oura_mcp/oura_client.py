"""Oura API client with OAuth2 token management."""

import httpx
from typing import Optional, Any

from .config import config


class OuraAPIError(Exception):
    """Base exception for Oura API errors."""

    def __init__(self, status_code: int, message: str, detail: Optional[str] = None):
        self.status_code = status_code
        self.message = message
        self.detail = detail
        super().__init__(
            f"[{status_code}] {message}: {detail}"
            if detail
            else f"[{status_code}] {message}"
        )


class OuraClient:
    """Client for interacting with Oura API v2."""

    BASE_URL = "https://api.ouraring.com"

    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize the Oura API client.

        Args:
            access_token: OAuth access token (optional, will use config if not provided)
        """
        self.config = config
        self._access_token = access_token
        self._client = httpx.Client(timeout=30.0)

    def __del__(self):
        """Cleanup HTTP client."""
        if hasattr(self, "_client"):
            self._client.close()

    def _get_headers(self) -> dict[str, str]:
        """Get authorization headers for API requests."""
        # Use provided token first, fall back to config
        token = self._access_token or self.config.access_token
        if not token:
            raise OuraAPIError(
                401,
                "No access token available",
                "Please configure OURA_ACCESS_TOKEN or authenticate via OAuth",
            )
        return {
            "Authorization": f"Bearer {token}",
        }

    def refresh_access_token(self) -> bool:
        """
        Refresh the access token using the refresh token.

        ⚠️  WARNING: OAuth2 token refresh is NOT TESTED YET!

        Returns:
            True if refresh was successful, False otherwise
        """
        if not self.config.refresh_token:
            return False

        if not (self.config.client_id and self.config.client_secret):
            return False

        try:
            response = self._client.post(
                f"{self.BASE_URL}/oauth/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.config.refresh_token,
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 200:
                data = response.json()
                new_access_token = data.get("access_token")
                new_refresh_token = data.get("refresh_token")

                if new_access_token and new_refresh_token:
                    self.config.save_tokens(new_access_token, new_refresh_token)
                    return True

            return False

        except Exception:
            return False

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        retry_on_401: bool = True,
    ) -> dict[str, Any]:
        """
        Make an authenticated request to the Oura API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            retry_on_401: Whether to attempt token refresh on 401 error

        Returns:
            JSON response data

        Raises:
            OuraAPIError: If the API returns an error
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()

        try:
            response = self._client.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
            )

            # Handle 401 errors with token refresh
            if response.status_code == 401 and retry_on_401:
                if self.refresh_access_token():
                    # Retry the request once with new token
                    return self._request(method, endpoint, params, retry_on_401=False)

            # Handle error responses
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    title = error_data.get("title", "API Error")
                    detail = error_data.get(
                        "detail", error_data.get("error_description")
                    )
                    raise OuraAPIError(response.status_code, title, detail)
                except (ValueError, KeyError):
                    raise OuraAPIError(
                        response.status_code,
                        f"HTTP {response.status_code}",
                        response.text or None,
                    )

            return response.json()

        except httpx.RequestError as e:
            raise OuraAPIError(0, "Request failed", str(e))

    def _handle_pagination(
        self, endpoint: str, params: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        """
        Handle paginated API responses.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            List of all items from paginated response
        """
        params = params or {}
        all_items = []

        while True:
            data = self._request("GET", endpoint, params)
            items = data.get("data", [])
            all_items.extend(items)

            # Check for next page
            next_token = data.get("next_token")
            if not next_token:
                break

            params["next_token"] = next_token

        return all_items

    # Personal Information
    def get_personal_info(self) -> dict[str, Any]:
        """Get user's personal information."""
        return self._request("GET", "/v2/usercollection/personal_info")

    # Daily Summaries
    def get_daily_sleep(
        self, start_date: str, end_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get daily sleep summaries.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional)
        """
        params = {"start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        return self._handle_pagination("/v2/usercollection/daily_sleep", params)

    def get_daily_activity(
        self, start_date: str, end_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get daily activity summaries.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional)
        """
        params = {"start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        return self._handle_pagination("/v2/usercollection/daily_activity", params)

    def get_daily_readiness(
        self, start_date: str, end_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get daily readiness summaries.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional)
        """
        params = {"start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        return self._handle_pagination("/v2/usercollection/daily_readiness", params)

    def get_daily_stress(
        self, start_date: str, end_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get daily stress summaries.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional)
        """
        params = {"start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        return self._handle_pagination("/v2/usercollection/daily_stress", params)

    def get_daily_spo2(
        self, start_date: str, end_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get daily SpO2 summaries (Gen 3 ring only).

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional)
        """
        params = {"start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        return self._handle_pagination("/v2/usercollection/daily_spo2", params)

    def get_daily_resilience(
        self, start_date: str, end_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get daily resilience summaries.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional)
        """
        params = {"start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        return self._handle_pagination("/v2/usercollection/daily_resilience", params)

    def get_daily_cardiovascular_age(
        self, start_date: str, end_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get daily cardiovascular age predictions.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional)
        """
        params = {"start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        return self._handle_pagination(
            "/v2/usercollection/daily_cardiovascular_age", params
        )

    # Detailed Sleep Data
    def get_sleep_periods(
        self, start_date: str, end_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get detailed sleep periods.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional)
        """
        params = {"start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        return self._handle_pagination("/v2/usercollection/sleep", params)

    def get_sleep_time(
        self, start_date: str, end_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get optimal bedtime recommendations.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional)
        """
        params = {"start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        return self._handle_pagination("/v2/usercollection/sleep_time", params)

    # Activity & Workouts
    def get_workouts(
        self, start_date: str, end_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get workout summaries.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional)
        """
        params = {"start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        return self._handle_pagination("/v2/usercollection/workout", params)

    def get_sessions(
        self, start_date: str, end_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get session data (meditation, breathing, etc.).

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional)
        """
        params = {"start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        return self._handle_pagination("/v2/usercollection/session", params)

    # Time-Series Data
    def get_heartrate(
        self, start_datetime: str, end_datetime: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get heart rate time-series data (5-minute intervals).

        Args:
            start_datetime: Start datetime in ISO 8601 format
            end_datetime: End datetime in ISO 8601 format (optional)
        """
        params = {"start_datetime": start_datetime}
        if end_datetime:
            params["end_datetime"] = end_datetime
        return self._handle_pagination("/v2/usercollection/heartrate", params)

    # User Annotations
    def get_enhanced_tags(
        self, start_date: str, end_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get user-entered enhanced tags.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional)
        """
        params = {"start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        return self._handle_pagination("/v2/usercollection/enhanced_tag", params)

    # Device Information
    def get_ring_configuration(self) -> list[dict[str, Any]]:
        """Get ring configuration and device information."""
        return self._handle_pagination("/v2/usercollection/ring_configuration")

    def get_rest_mode_periods(
        self, start_date: str, end_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get rest mode periods.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional)
        """
        params = {"start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        return self._handle_pagination("/v2/usercollection/rest_mode_period", params)

    # Fitness Metrics
    def get_vo2_max(
        self, start_date: str, end_date: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Get VO2 max estimates.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional)
        """
        params = {"start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        return self._handle_pagination("/v2/usercollection/vO2_max", params)
