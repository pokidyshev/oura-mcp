# Oura API v2 - LLM Reference Guide

## Overview

The Oura API provides programmatic access to health data from Oura Ring devices including sleep, activity, readiness, heart rate, and other biometric metrics. This is the only available API version (V1 has been sunset).

**Base URL:** `https://api.ouraring.com`
**Authentication:** OAuth2 (Bearer token)
**Rate Limit:** 5000 requests per 5-minute period

## Authentication

### OAuth2 URLs

- **Authorization:** `https://cloud.ouraring.com/oauth/authorize`
- **Token Exchange:** `https://api.ouraring.com/oauth/token`
- **Token Revocation:** `https://api.ouraring.com/oauth/revoke?access_token={token}`

### Available Scopes

- `email` - Email address
- `personal` - Personal info (age, height, weight, gender)
- `daily` - Daily summaries (sleep, activity, readiness)
- `heartrate` - Time-series heart rate data
- `workout` - Workout summaries
- `tag` - User-entered tags
- `session` - Guided/unguided sessions
- `spo2Daily` - SpO2 averages during sleep

**Note:** Users can enable/disable individual scopes during authorization. Request only needed scopes.

### Server-Side Flow (Recommended - with refresh tokens)

#### Step 1: Authorization Request

```
GET https://cloud.ouraring.com/oauth/authorize?
  response_type=code&
  client_id=YOUR_CLIENT_ID&
  redirect_uri=https%3A%2F%2Fexample.com%2Fcallback&
  state=RANDOM_STRING&
  scope=email+personal+daily
```

**Parameters:**

- `response_type` (required): Must be `code`
- `client_id` (required): Your application's client ID
- `redirect_uri` (optional but recommended): URL-encoded callback URL (must match registered URIs)
- `state` (optional but recommended): Random string for CSRF protection, returned unchanged
- `scope` (optional): Space-separated scopes (defaults to all if omitted)

#### Step 2: User Authorization

User logs in and grants/denies access. Oura redirects to your `redirect_uri`:

**Success:**

```
GET https://example.com/callback?
  code=AUTH_CODE&
  scope=email+personal&
  state=RANDOM_STRING
```

**Denial:**

```
GET https://example.com/callback?
  error=access_denied&
  state=RANDOM_STRING
```

**Note:** Authorization code is valid for 10 minutes and single-use only.

#### Step 3: Exchange Code for Token

```
POST https://api.ouraring.com/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=AUTH_CODE&
redirect_uri=https://example.com/callback&
client_id=YOUR_CLIENT_ID&
client_secret=YOUR_CLIENT_SECRET
```

**Alternative:** Use HTTP Basic Auth with client_id as username and client_secret as password.

**Response:**

```json
{
  "token_type": "bearer",
  "access_token": "ACCESS_TOKEN",
  "expires_in": 86400,
  "refresh_token": "REFRESH_TOKEN"
}
```

#### Step 4: Refresh Token (when access token expires)

```
POST https://api.ouraring.com/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&
refresh_token=REFRESH_TOKEN&
client_id=YOUR_CLIENT_ID&
client_secret=YOUR_CLIENT_SECRET
```

**Response:** New access_token AND new refresh_token (single-use refresh tokens)

### Client-Side Flow (No refresh tokens)

**Note:** Tokens expire after 30 days; re-authorization required after expiry.

#### Step 1: Authorization Request

```
GET https://cloud.ouraring.com/oauth/authorize?
  response_type=token&
  client_id=YOUR_CLIENT_ID&
  redirect_uri=https%3A%2F%2Fexample.com%2Fcallback&
  state=RANDOM_STRING&
  scope=email+personal
```

**Parameters:** Same as server-side except `response_type=token`

#### Step 2: Token in Redirect Fragment

Oura redirects with token in URL fragment (after #):

**Success:**

```
https://example.com/callback#
  token_type=bearer&
  access_token=ACCESS_TOKEN&
  expires_in=2592000&
  scope=email+personal&
  state=RANDOM_STRING
```

**Denial:**

```
https://example.com/callback?error=access_denied&state=RANDOM_STRING
```

### Using Access Tokens

Include in Authorization header for all API requests:

```
GET /v2/usercollection/sleep HTTP/1.1
Host: api.ouraring.com
Authorization: Bearer ACCESS_TOKEN
```

### Token Management

**Access Token Expiration:**

- Server-side flow: ~24 hours (86400 seconds)
- Client-side flow: 30 days (2592000 seconds)

**Refresh Token:**

- Single-use only (invalidated after use)
- New refresh token provided with each refresh
- Only available in server-side flow

**Token Revocation:**

```
GET https://api.ouraring.com/oauth/revoke?access_token=ACCESS_TOKEN
```

**Best Practices:**

- Store tokens securely (encrypted database, never in client code)
- Implement automatic token refresh before expiration
- Use HTTPS for all OAuth2 flows
- Always include `state` parameter for CSRF protection
- Handle 401 errors by refreshing token automatically

## Best Practices

### Data Access Pattern (RECOMMENDED)

1. **Initial setup:** Single request for historical data when user connects
2. **Ongoing updates:** Use webhooks (see Webhooks section)
3. **Result:** No rate limit issues - webhook users don't hit limits

### Data Sync Timing

- **User-initiated sync** (requires opening app):
  - Sleep data
  - Readiness
  - Sleep time recommendations
- **Background sync** (periodic):
  - Daily activity
  - Daily stress
  - Heart rate

### Webhooks (STRONGLY RECOMMENDED)

- Notifications arrive ~30 seconds after mobile app sync
- Create subscriptions per data_type + event_type combination
- Verify HMAC signatures for security
- Respond within 10 seconds with 2xx/3xx status
- Use webhook events to fetch only updated data

## Core Endpoints

### Personal Information

**GET** `/v2/usercollection/personal_info`

- Returns: `id`, `age`, `weight`, `height`, `biological_sex`, `email`
- Scope: Any token (for `id`), `personal` (for other fields)

### Daily Summaries

**GET** `/v2/usercollection/daily_activity`

- Params: `start_date`, `end_date`, `next_token` (pagination)
- Returns: Activity score, MET minutes, calories, steps, class_5_min (activity levels)
- Scope: `daily`

**GET** `/v2/usercollection/daily_sleep`

- Params: `start_date`, `end_date`, `next_token`
- Returns: Sleep score, contributors (deep_sleep, efficiency, latency, rem_sleep, restfulness, timing, total_sleep)
- Scope: `daily`

**GET** `/v2/usercollection/daily_readiness`

- Params: `start_date`, `end_date`, `next_token`
- Returns: Readiness score, contributors (activity_balance, body_temperature, hrv_balance, previous_day_activity, previous_night, recovery_index, resting_heart_rate, sleep_balance)
- Scope: `daily`

**GET** `/v2/usercollection/daily_stress`

- Params: `start_date`, `end_date`, `next_token`
- Returns: `stress_high` (seconds), `recovery_high` (seconds), `day_summary` (restored/normal/stressful)
- Scope: `daily`

**GET** `/v2/usercollection/daily_spo2`

- Params: `start_date`, `end_date`, `next_token`
- Returns: Average SpO2 percentage, breathing disturbance index
- Scope: `spo2Daily`
- Note: Gen 3 ring only

**GET** `/v2/usercollection/daily_resilience`

- Params: `start_date`, `end_date`, `next_token`
- Returns: Resilience level (limited/adequate/solid/strong/exceptional), contributors
- Scope: `daily`

**GET** `/v2/usercollection/daily_cardiovascular_age`

- Params: `start_date`, `end_date`, `next_token`
- Returns: Predicted vascular age [18-100]
- Scope: `daily`

### Detailed Sleep Data

**GET** `/v2/usercollection/sleep`

- Params: `start_date`, `end_date`, `next_token`
- Returns: Detailed sleep periods including:
  - Timing: `bedtime_start`, `bedtime_end`, `day`
  - Durations: `total_sleep_duration`, `awake_time`, `deep_sleep_duration`, `light_sleep_duration`, `rem_sleep_duration`, `latency`
  - Biometrics: `average_heart_rate`, `lowest_heart_rate`, `average_hrv`, `average_breath`
  - Classifications: `sleep_phase_5_min` (1=deep, 2=light, 3=REM, 4=awake), `movement_30_sec` (1=none, 2=restless, 3=tossing, 4=active)
  - Metadata: `efficiency`, `sleep_algorithm_version` (v1/v2), `type` (sleep/long_sleep/late_nap/rest/deleted)
- Scope: `daily`
- Note: Multiple sleep periods possible per day

**GET** `/v2/usercollection/sleep/{document_id}`

- Returns: Single sleep document by ID

**GET** `/v2/usercollection/sleep_time`

- Params: `start_date`, `end_date`, `next_token`
- Returns: Optimal bedtime recommendations, status, recommendation actions
- Scope: `daily`

### Activity & Workouts

**GET** `/v2/usercollection/workout`

- Params: `start_date`, `end_date`, `next_token`
- Returns: Workout details including:
  - `activity` (type), `intensity` (easy/moderate/hard)
  - `calories`, `distance`, `start_datetime`, `end_datetime`
  - `source` (manual/autodetected/confirmed/workout_heart_rate)
  - `label` (optional user-defined)
- Scope: `workout`

**GET** `/v2/usercollection/session`

- Params: `start_date`, `end_date`, `next_token`
- Returns: Moment/session data including:
  - `type` (breathing/meditation/nap/relaxation/rest/body_status)
  - Time-series: `heart_rate`, `heart_rate_variability`, `motion_count`
  - `mood` (bad/worse/same/good/great)
- Scope: `session`

### Time-Series Data

**GET** `/v2/usercollection/heartrate`

- Params: `start_datetime`, `end_datetime`, `next_token`
- Returns: 5-minute interval heart rate data
- Fields: `bpm`, `source` (awake/rest/sleep/session/live/workout), `timestamp`
- Scope: `heartrate`
- Note: Use datetime (not date) parameters

### User Annotations

**GET** `/v2/usercollection/tag`

- Params: `start_date`, `end_date`, `next_token`
- Returns: User tags with `text`, `tags` array, `timestamp`
- Scope: `tag`
- Note: DEPRECATED - use enhanced_tag instead

**GET** `/v2/usercollection/enhanced_tag`

- Params: `start_date`, `end_date`, `next_token`
- Returns: Enhanced tags with:
  - `tag_type_code`, `custom_name`
  - `start_time`, `end_time`, `start_day`, `end_day`
  - `comment`
- Scope: `tag`
- Note: Supports duration-based tags

### Device Information

**GET** `/v2/usercollection/ring_configuration`

- Params: `next_token`
- Returns: Ring details including:
  - `color`, `design` (balance/balance_diamond/heritage/horizon)
  - `hardware_type` (gen1/gen2/gen2m/gen3/gen4)
  - `size`, `firmware_version`, `set_up_at`
- Scope: Any token

**GET** `/v2/usercollection/rest_mode_period`

- Params: `start_date`, `end_date`, `next_token`
- Returns: Rest mode periods with `start_day`, `end_day`, `episodes` (array of tags)
- Scope: `daily`

### Fitness Metrics

**GET** `/v2/usercollection/vO2_max`

- Params: `start_date`, `end_date`, `next_token`
- Returns: VO2 max estimates with `vo2_max`, `day`, `timestamp`
- Scope: `daily`

## Webhooks

### Subscription Management

**GET** `/v2/webhook/subscription`

- Headers: `x-client-id`, `x-client-secret`
- Returns: List of webhook subscriptions

**POST** `/v2/webhook/subscription`

- Headers: `x-client-id`, `x-client-secret`
- Body: `callback_url`, `verification_token`, `event_type`, `data_type`
- Event types: `create`, `update`, `delete`
- Data types: All endpoint types (sleep, daily_activity, etc.)

**GET** `/v2/webhook/subscription/{id}`

- Returns: Single subscription details

**PUT** `/v2/webhook/subscription/{id}`

- Updates existing subscription

**DELETE** `/v2/webhook/subscription/{id}`

- Removes subscription

**PUT** `/v2/webhook/subscription/renew/{id}`

- Renews expiring subscription

### Webhook Verification Flow

1. POST subscription request → Oura sends GET to callback_url
2. Callback receives: `?verification_token=X&challenge=Y`
3. Callback responds: `{"challenge": "Y"}`
4. Subscription activated

### Webhook Event Structure

```json
{
  "event_type": "update",
  "data_type": "sleep",
  "object_id": "12345abc",
  "event_time": "2023-01-01T08:00:00+00:00",
  "user_id": "user123"
}
```

### Security

- Verify HMAC signature in `x-oura-signature` header
- Algorithm: HMAC-SHA256 of `timestamp + JSON.stringify(body)`
- Key: Your client_secret

## Common Data Structures

### Timestamps

- Format: ISO 8601 with timezone
- Types: `LocalDateTime`, `LocalizedDateTime`, `UtcDateTime`

### Scores

- Range: 1-100 (higher = better)
- Null values possible if insufficient data

### Contributors

- Range: 1-100 per contributor
- Show relative impact on overall score

### Sample Data

```json
{
  "interval": 300, // seconds between samples
  "items": [65, 64, null, 66], // null = missing data
  "timestamp": "2023-01-01T00:00:00.000+00:00"
}
```

### Pagination

- Use `next_token` from response in next request
- Null `next_token` = no more data

## Sandbox Endpoints

For testing without real user data, use sandbox endpoints:

- Pattern: `/v2/sandbox/usercollection/{endpoint}`
- Example: `/v2/sandbox/usercollection/sleep`
- Same authentication required
- Returns fake but realistic data
- Shares rate limit with production endpoints

## HTTP Response Codes

- `200` - Success
- `201` - Created (webhook subscriptions)
- `204` - No content (successful deletion)
- `400` - Invalid query parameters
- `401` - Invalid/expired token
- `403` - Insufficient permissions or expired subscription
- `404` - Resource not found
- `422` - Validation error
- `429` - Rate limit exceeded (5000 requests per 5 minutes)

## Error Handling

### Standard Error Response Format (RFC7807)

All API errors return JSON with these fields:

```json
{
  "status": 400,
  "title": "Brief error summary",
  "detail": "Detailed explanation of this specific error occurrence"
}
```

**Fields:**

- `status` (always): HTTP status code (400-599)
- `title` (always): Short, human-readable error description
- `detail` (optional): Specific explanation for this error instance

### OAuth2 Error Response Format (RFC6749)

OAuth2 endpoints include additional fields:

```json
{
  "status": 401,
  "title": "Invalid Access Token",
  "error": "invalid_token",
  "error_description": "Access token not provided or is invalid",
  "detail": "Access token not provided or is invalid",
  "error_uri": "https://example.com/error-docs"
}
```

**Additional OAuth2 Fields:**

- `error` (always): Standard OAuth2 error code
- `error_description` (optional): Human-readable details
- `error_uri` (optional): URL to error documentation

### Common Error Scenarios

#### Authentication Errors (401)

**Invalid Access Token**

- Error: `invalid_token`
- Cause: Token malformed, incomplete, or invalid
- Fix: Verify token format and completeness

**Expired Token**

- Error: `invalid_token`
- Cause: Access token has expired (>24 hours old for server-side)
- Fix: Use refresh token to get new access token

**Token Already Used or Revoked**

- Error: `invalid_grant`
- Cause: Refresh token was already used (single-use) or revoked by user
- Fix: Use the new refresh token from previous refresh, or re-authorize if revoked

**Missing Token**

- Error: `invalid_token`
- Cause: Authorization header missing or malformed
- Fix: Include `Authorization: Bearer TOKEN` header

#### Authorization Errors (403)

**Missing Scopes**

- Cause: Token doesn't have required scope for endpoint
- Detail: Lists required scopes
- Fix: Re-authorize with needed scopes

**Expired Subscription**

- Cause: User's Oura membership has expired
- Fix: User must renew Oura subscription

**Webhook Not Found**

- Cause: Webhook subscription ID doesn't exist
- Fix: Verify subscription ID or create new subscription

#### Request Errors (400)

**Invalid Query Parameters**

- Cause: Malformed dates, invalid next_token, or incorrect parameter format
- Fix: Check parameter format (dates: YYYY-MM-DD, datetimes: ISO 8601)

**Missing Required Parameter**

- Error: `invalid_request`
- Cause: Required OAuth2 parameter missing
- Fix: Check all required parameters are included

#### Validation Errors (422)

**Invalid Request Body**

- Cause: Webhook subscription body has invalid fields
- Response includes: `detail` array with validation errors per field
- Fix: Correct request body format

#### Rate Limit Errors (429)

**Request Rate Limit Exceeded**

- Cause: >5000 requests in 5-minute rolling window
- Fix: Implement exponential backoff, use webhooks (recommended)
- Contact: api-support@ouraring.com for higher limits

#### Not Found Errors (404)

**Document Not Found**

- Cause: Requested document_id doesn't exist
- Fix: Verify ID or check if user has data for that period

### OAuth2-Specific Error Codes

**Standard Error Values:**

- `invalid_request` - Missing/invalid required parameter
- `invalid_client` - Client authentication failed (wrong client_id/secret)
- `invalid_grant` - Code expired/invalid/revoked, or redirect_uri mismatch
- `unauthorized_client` - Client not authorized by Oura
- `unsupported_grant_type` - grant_type not supported (must be authorization_code or refresh_token)
- `invalid_scope` - Requested scope invalid or exceeds available scopes
- `invalid_token` - Token expired, revoked, malformed, or invalid
- `access_denied` - User denied authorization request
- `unsupported_response_type` - response_type not supported
- `server_error` - Server encountered unexpected error
- `temporarily_unavailable` - Server temporarily unavailable

### Error Handling Best Practices

1. **401 Errors:** Automatically attempt token refresh before re-prompting user
2. **403 Scope Errors:** Show user which permissions are needed and why
3. **429 Rate Limits:** Implement exponential backoff (start with 1s, double each retry)
4. **5xx Errors:** Retry with exponential backoff (transient server issues)
5. **Invalid Grant:** Clear stored tokens and re-initiate OAuth2 flow
6. **Webhook Failures:** Oura retries 10 times; respond with 410 to auto-cancel subscription
7. **Token Storage:** Always handle case where tokens are null/undefined
8. **Error Logging:** Log full error response for debugging, not just status code

## Common Patterns

### Date Range Query

```
GET /v2/usercollection/daily_activity?start_date=2023-01-01&end_date=2023-01-31
```

### Datetime Range Query (for time-series)

```
GET /v2/usercollection/heartrate?start_datetime=2023-01-01T00:00:00-08:00&end_datetime=2023-01-02T00:00:00-08:00
```

### Pagination

```
GET /v2/usercollection/sleep?start_date=2023-01-01&next_token=abc123
```

### Single Document

```
GET /v2/usercollection/sleep/12345abc
```

## Data Types Reference

### Activity Classifications (5-min intervals)

- `0` - Non-wear
- `1` - Rest
- `2` - Inactive
- `3` - Low activity
- `4` - Medium activity
- `5` - High activity

### Sleep Phases (5-min intervals)

- `1` - Deep sleep
- `2` - Light sleep
- `3` - REM sleep
- `4` - Awake

### Movement (30-sec intervals)

- `1` - No motion
- `2` - Restless
- `3` - Tossing and turning
- `4` - Active

### Workout Intensities

- `easy`
- `moderate`
- `hard`

### Workout Sources

- `manual` - User-entered
- `autodetected` - Automatically detected
- `confirmed` - User confirmed auto-detection
- `workout_heart_rate` - Detected via heart rate

### Session Types

- `breathing`
- `meditation`
- `nap`
- `relaxation`
- `rest`
- `body_status`

### Heart Rate Sources

- `awake` - Daytime measurement
- `rest` - Resting measurement
- `sleep` - During sleep
- `session` - During guided session
- `live` - Live measurement
- `workout` - During workout

## Key Metrics Explained

### MET (Metabolic Equivalent)

- 1 MET = resting metabolic rate
- Higher MET = more intense activity
- MET minutes = intensity × duration

### HRV (Heart Rate Variability)

- Time variation between heartbeats
- Higher = better recovery/readiness
- Measured in milliseconds

### SpO2

- Blood oxygen saturation percentage
- Normal range: 95-100%
- Gen 3 ring only

### Sleep Efficiency

- Percentage of time in bed spent sleeping
- Higher = better sleep quality

### Readiness Score

- Holistic measure of recovery
- Considers sleep, activity, HRV, temperature

### Activity Score

- Daily activity performance
- Considers movement, calories, targets

## Important Notes

1. **Token Expiration:** Access tokens expire ~24 hours, refresh proactively
2. **Subscription Limits:** 10 users without approval, unlimited after approval
3. **User Consent:** Users must grant permission for each data scope
4. **Data Availability:** Depends on sync frequency (app opening for sleep data)
5. **Webhook Expiry:** Subscriptions expire after ~90 days, renew proactively
6. **Multiple Sleep Periods:** Users can have multiple sleep/nap sessions per day
7. **Null Values:** Missing data indicated by null, not zero
8. **Timezone Handling:** Dates interpreted in user's local timezone
9. **Historical Data:** Backfill limit varies by data type, typically months-years
10. **Rate Limit Reset:** 5-minute rolling window, not fixed intervals

## Support Resources

- API Application Registration: https://cloud.ouraring.com/oauth/applications
- Terms of Service: https://cloud.ouraring.com/legal/api-agreement
- Support Email: api-support@ouraring.com

---

**Version:** 2.0 (v1.27 OpenAPI spec)
**Last Updated:** 2025
