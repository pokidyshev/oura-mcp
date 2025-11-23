# Oura MCP

A comprehensive Model Context Protocol (MCP) server for the Oura Ring API v2, providing LLMs like Claude with seamless access to sleep, activity, readiness, heart rate, and other health metrics from your Oura Ring.

## Features

- **🔧 15+ MCP Tools**: Interactive data fetching with flexible date ranges
- **📊 5 MCP Resources**: Quick access to recent summaries without parameters
- **🔄 OAuth2 Token Management**: Automatic token refresh with persistent storage
- **📅 Natural Language Dates**: Support for "today", "yesterday", "last week"
- **🛡️ Comprehensive Error Handling**: Graceful handling of API errors with detailed messages
- **📖 Complete API Coverage**: All major Oura API v2 endpoints

## Available Tools

### Core Daily Summaries

- `get_daily_sleep` - Sleep scores and contributors (deep sleep, REM, efficiency, etc.)
- `get_daily_activity` - Activity scores, steps, calories, and MET minutes
- `get_daily_readiness` - Readiness scores with HRV, temperature, and recovery metrics
- `get_daily_stress` - Stress and recovery time in seconds

### Detailed Sleep Data

- `get_sleep_periods` - Detailed sleep sessions with phases, heart rate, HRV, breathing
- `get_sleep_time` - Optimal bedtime recommendations

### Activity & Workouts

- `get_workouts` - Workout summaries with type, intensity, calories, distance
- `get_sessions` - Meditation, breathing exercises, and nap sessions

### Time-Series Data

- `get_heartrate` - 5-minute interval heart rate measurements

### Advanced Metrics

- `get_daily_spo2` - Blood oxygen levels during sleep (Gen 3 ring)
- `get_vo2_max` - VO2 max cardiorespiratory fitness estimates
- `get_daily_resilience` - Resilience scores and levels
- `get_cardiovascular_age` - Predicted vascular age [18-100]

### User Data

- `get_personal_info` - Age, weight, height, biological sex, email
- `get_ring_configuration` - Ring model, color, size, firmware version
- `get_enhanced_tags` - User-entered tags and annotations
- `get_rest_mode_periods` - Rest mode periods

## Available Resources

Quick access to recent data without parameters:

- `oura://summary/today` - Today's readiness, sleep, and activity scores
- `oura://summary/yesterday` - Yesterday's complete summary
- `oura://personal/info` - Personal information and ring configuration
- `oura://recent/sleep` - Last 7 days of sleep scores
- `oura://recent/activity` - Last 7 days of activity scores

## Prerequisites

1. **Oura Ring Account**: Active Oura Ring with synced data
2. **Personal Access Token**: Get it from [Oura Cloud](https://cloud.ouraring.com/personal-access-tokens)

That's it! For personal use, a Personal Access Token is all you need.

### Getting Your Personal Access Token (Recommended - 2 minutes)

1. Go to https://cloud.ouraring.com/personal-access-tokens
2. Log in with your Oura account
3. Click "Create A New Personal Access Token"
4. Give it a name (e.g., "MCP Server")
5. Copy the token (you won't see it again!)

**Note**: Personal Access Tokens don't expire but can be revoked. Perfect for personal use!

### OAuth2 Setup (Advanced - For Production Apps)

Only needed if you're building a production application that requires automatic token refresh.

1. Go to https://cloud.ouraring.com/oauth/applications
2. Create a new application
3. Note your `Client ID` and `Client Secret`
4. Complete the OAuth2 flow to get access and refresh tokens

For detailed OAuth2 flow, see [Oura API Documentation](https://cloud.ouraring.com/docs/authentication).

## Installation & Setup

### For Claude Desktop

1. **Get your Oura Personal Access Token**:

   - Go to https://cloud.ouraring.com/personal-access-tokens
   - Create a new token
   - Copy it immediately (you won't see it again!)

2. **Configure Claude Desktop**:

   Edit your Claude Desktop config file:

   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

   Add the server configuration:

   ```json
   {
     "mcpServers": {
       "oura": {
         "command": "uvx",
         "args": ["oura-mcp"],
         "env": {
           "OURA_ACCESS_TOKEN": "YOUR_PERSONAL_ACCESS_TOKEN_HERE"
         }
       }
     }
   }
   ```

   **For OAuth2 with auto-refresh** (advanced), include all four variables:

   ```json
   {
     "mcpServers": {
       "oura": {
         "command": "uvx",
         "args": ["oura-mcp"],
         "env": {
           "OURA_ACCESS_TOKEN": "YOUR_ACCESS_TOKEN_HERE",
           "OURA_REFRESH_TOKEN": "YOUR_REFRESH_TOKEN_HERE",
           "OURA_CLIENT_ID": "YOUR_CLIENT_ID_HERE",
           "OURA_CLIENT_SECRET": "YOUR_CLIENT_SECRET_HERE"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop**

4. **Verify**: Look for the 🔌 icon in Claude - you should see the Oura server connected

### For Development

1. **Clone or create the project**:

   ```bash
   git clone <repository-url>
   cd oura-mcp
   ```

2. **Create `.env` file**:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Personal Access Token:

   ```
   OURA_ACCESS_TOKEN=your_personal_access_token_here
   ```

   (For OAuth2 setup, see the comments in `.env.example`)

3. **Install dependencies**:

   ```bash
   uv sync
   ```

4. **Test with MCP Inspector**:

   ```bash
   uv run mcp dev src/oura_mcp/server.py
   ```

   Open the provided URL (usually http://localhost:5173) to interact with the server.

## Configuration

### Environment Variables

| Variable             | Required | Description                                                     |
| -------------------- | -------- | --------------------------------------------------------------- |
| `OURA_ACCESS_TOKEN`  | **Yes**  | Personal Access Token or OAuth2 access token                    |
| `OURA_REFRESH_TOKEN` | No       | OAuth2 refresh token (for automatic token renewal)              |
| `OURA_CLIENT_ID`     | No\*     | OAuth2 client ID (\*required if using `OURA_REFRESH_TOKEN`)     |
| `OURA_CLIENT_SECRET` | No\*     | OAuth2 client secret (\*required if using `OURA_REFRESH_TOKEN`) |
| `OURA_TOKEN_FILE`    | No       | Path to token storage file (default: `.oura_tokens.json`)       |

### Authentication Methods

**Method 1: Personal Access Token (Recommended)**

- ✅ Simple setup - just one token
- ✅ No expiration (unless you revoke it)
- ✅ Perfect for personal use
- ❌ Must manually revoke/recreate if compromised

```bash
OURA_ACCESS_TOKEN=your_personal_access_token
```

**Method 2: OAuth2 with Refresh Tokens (Advanced)**

- ✅ Automatic token refresh
- ✅ Tokens expire regularly (more secure)
- ✅ Better for production applications
- ❌ More complex setup (4 variables)

```bash
OURA_ACCESS_TOKEN=your_oauth2_access_token
OURA_REFRESH_TOKEN=your_refresh_token
OURA_CLIENT_ID=your_client_id
OURA_CLIENT_SECRET=your_client_secret
```

### Token Management

**Personal Access Token:**

- Does not expire automatically
- Can be revoked at https://cloud.ouraring.com/personal-access-tokens
- No automatic refresh needed

**OAuth2 Tokens:**

- **Automatic Refresh**: If you provide all OAuth2 credentials, the server will automatically refresh your access token when it expires (typically after 24 hours)
- **Token Persistence**: Updated tokens are automatically saved to `.oura_tokens.json` for persistence across restarts
- **Manual Refresh**: If only access token is provided, you'll need to manually update it when it expires

## Usage Examples

### Using with Claude

Once configured, you can ask Claude natural questions like:

- "What was my sleep score last night?"
- "Show me my activity data for the past week"
- "How is my readiness trending over the last month?"
- "What was my heart rate during my workout yesterday?"
- "Show me my VO2 max progression"

### Tool Parameters

Most tools accept flexible date parameters:

```python
# Natural language
get_daily_sleep(start_date="today")
get_daily_sleep(start_date="yesterday")
get_daily_sleep(start_date="last week")

# Specific dates
get_daily_sleep(start_date="2024-01-01", end_date="2024-01-31")

# Default (last week if not specified)
get_daily_sleep()
```

### Resource Access

Resources provide instant access without parameters:

- Simply reference `oura://summary/today` to get today's summary
- Use `oura://recent/sleep` for the last week of sleep data

## API Rate Limits

The Oura API has a rate limit of **5,000 requests per 5-minute rolling window**. This server handles:

- Automatic pagination for large datasets
- Error messages when rate limits are exceeded
- Efficient resource caching where appropriate

**Best Practice**: Use webhooks (not included in this server) for real-time updates instead of frequent polling.

## Troubleshooting

### "No access token available" error

**Solution**: Ensure `OURA_ACCESS_TOKEN` is set in your environment or `.env` file.

Get a Personal Access Token from: https://cloud.ouraring.com/personal-access-tokens

### Token expired (401 error)

**For Personal Access Token users:**

- Personal Access Tokens don't expire unless revoked
- If you get this error, your token may have been revoked
- Create a new token at https://cloud.ouraring.com/personal-access-tokens

**For OAuth2 users:**

1. If you have all OAuth2 credentials configured, the server will automatically refresh it
2. If not, manually obtain a new access token and update your configuration

### "Missing scopes" error (403)

**Solution**: Re-authorize your application with the required scopes. The error message will indicate which scopes are needed.

### Rate limit exceeded (429 error)

**Solution**: Wait for the rate limit window to reset (5 minutes). Consider:

- Reducing query frequency
- Using date ranges instead of multiple single-day queries
- Implementing webhooks for real-time data (not included in this server)

### Connection issues

**Solutions**:

1. Check your internet connection
2. Verify Oura API is accessible: https://api.ouraring.com
3. Ensure your access token is valid

### Data not available (404)

**Cause**: The requested data doesn't exist for the specified date range.

**Solutions**:

- Ensure your Oura Ring has synced recently (requires opening the mobile app)
- Check that you're querying dates when you were wearing the ring
- Some metrics require Gen 3 ring (e.g., SpO2)

## Data Availability Notes

- **Sleep data**: Requires manual sync via mobile app
- **Activity data**: Syncs automatically in background
- **Real-time data**: Not available; data appears after sync
- **Historical data**: Available for several months to years depending on metric

## Security

- **Token Storage**:
  - Personal Access Tokens are stored in environment variables only
  - OAuth2 tokens are stored locally in `.oura_tokens.json` (add to `.gitignore`)
- **Secure Transport**: All API calls use HTTPS
- **No Data Collection**: This server only communicates with Oura's API
- **Token Permissions**: Personal Access Tokens have full account access; OAuth2 tokens can be scoped

## Required API Scopes

This server requires the following Oura API scopes:

- `personal` - Personal information (age, weight, height)
- `daily` - Daily summaries (sleep, activity, readiness, stress)
- `heartrate` - Heart rate time-series data
- `workout` - Workout summaries
- `session` - Meditation and breathing sessions
- `tag` - User tags and annotations
- `spo2Daily` - SpO2 data (if using Gen 3 ring)

## Development

### Running Tests

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest
```

### Building

```bash
uv build
```

### Publishing

```bash
uv publish
```

## Architecture

```
oura-mcp/
├── src/oura_mcp/
│   ├── __init__.py          # Package initialization
│   ├── server.py            # MCP server with tools and resources
│   ├── oura_client.py       # Oura API client with OAuth2
│   └── config.py            # Configuration management
├── pyproject.toml           # Project metadata and dependencies
├── README.md                # This file
└── .env.example             # Example environment variables
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- **Oura API Documentation**: https://cloud.ouraring.com/docs
- **Oura API Support**: api-support@ouraring.com
- **MCP Documentation**: https://modelcontextprotocol.io

## Changelog

### v0.1.0 (Initial Release)

- Complete Oura API v2 integration
- 15+ MCP tools for data fetching
- 5 MCP resources for quick access
- OAuth2 token management with auto-refresh
- Natural language date parsing
- Comprehensive error handling
- Token persistence across restarts

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Powered by [Oura API v2](https://cloud.ouraring.com/docs)
- Model Context Protocol by [Anthropic](https://modelcontextprotocol.io)
