# Oura MCP Server

Connect your Oura Ring to Claude, Cursor, or any MCP-compatible app! Ask questions about your sleep, activity, readiness, heart rate, and other health metrics using natural language.

## What Can You Do?

Once installed, you can ask your AI assistant:

- "What was my sleep score last night?"
- "Show me my activity data for the past week"
- "How is my readiness trending this month?"
- "What was my heart rate during yesterday's workout?"
- "Show me my VO2 max progression"

Your AI assistant will have access to all your Oura Ring data and can analyze trends, compare periods, and give you insights.

## Quick Setup

### Step 1: Get Your Oura Token

1. Go to https://cloud.ouraring.com/personal-access-tokens
2. Log in with your Oura account
3. Click **"Create A New Personal Access Token"**
4. Give it a name (like "Claude")
5. **Copy the token** - you won't see it again!

### Step 2: Configure Your MCP Client

**For Claude Desktop:**

Find your Claude Desktop config file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Open it in a text editor and add this (replace `YOUR_TOKEN_HERE` with your token from Step 1):

```json
{
  "mcpServers": {
    "oura": {
      "command": "uvx",
      "args": ["oura-mcp"],
      "env": {
        "OURA_ACCESS_TOKEN": "YOUR_TOKEN_HERE"
      }
    }
  }
}
```

**If you already have other MCP servers**, just add the `"oura"` section inside `"mcpServers"`.

**For other MCP clients** (Cursor, etc.): Refer to your client's documentation for MCP server configuration. Use the same `uvx oura-mcp` command with the `OURA_ACCESS_TOKEN` environment variable.

### Step 3: Restart Your MCP Client

Close and reopen your application (Claude Desktop, Cursor, etc.). Look for the MCP servers/tools indicator - you should see "oura" listed as connected.

### Step 4: Start Using It!

Try asking: "Show me my sleep data from last week"

## Available Data

The server provides access to:

**Daily Summaries**

- Sleep scores and analysis (deep sleep, REM, efficiency, etc.)
- Activity scores, steps, calories, and active time
- Readiness scores with HRV, temperature, and recovery metrics
- Stress and recovery data

**Detailed Metrics**

- Sleep sessions with heart rate, HRV, and breathing patterns
- Workouts with intensity, calories, and distance
- Heart rate data in 5-minute intervals
- VO2 max estimates
- Blood oxygen levels (Gen 3 ring)
- Resilience and cardiovascular age

**Personal Data**

- Ring information and settings
- Personal profile data
- Tags and annotations

## Troubleshooting

### "No access token available" or connection error

1. Double-check your token is correct in the config file
2. Make sure there are no extra spaces or quotes
3. Restart your application after making changes
4. Create a new token if needed: https://cloud.ouraring.com/personal-access-tokens

### No data showing up

- Make sure your Oura Ring has synced recently (open the Oura mobile app)
- Sleep data requires manual sync via the app
- You can only access dates when you were wearing the ring

### MCP client doesn't see the Oura server

1. Check your client's MCP servers/tools list - is "oura" listed?
2. Verify your config file has valid JSON (use a JSON validator online)
3. Make sure you restarted your application after editing the config

### Still having issues?

Check the Oura API status: https://api.ouraring.com

## For Developers

### Local Development

```bash
git clone https://github.com/pokidyshev/oura-mcp.git
cd oura-mcp

# Create .env file with your token
cp .env.example .env
# Edit .env and add: OURA_ACCESS_TOKEN=your_token

# Install and test
uv sync
uv run mcp dev src/oura_mcp/server.py
```

### OAuth2 Support

⚠️ **OAuth2 with automatic token refresh is implemented but NOT TESTED YET.**

For production applications needing OAuth2, see `.env.example` for configuration options. Pull requests welcome to help test and document this feature!

## Technical Details

- **Rate Limits**: 5,000 requests per 5-minute window (handled automatically)
- **Data Format**: All responses in JSON
- **Date Formats**: Supports natural language ("today", "yesterday", "last week") and YYYY-MM-DD
- **Security**: All API calls use HTTPS. Tokens stored in environment variables only.

## License

MIT License - see LICENSE file

## Links

- **Oura API Documentation**: https://cloud.ouraring.com/docs
- **MCP Documentation**: https://modelcontextprotocol.io
- **Built with**: [FastMCP](https://github.com/jlowin/fastmcp)
