# Weather MCP — Israel 🇮🇱 & USA 🇺🇸

A terminal chat app powered by Claude that retrieves weather forecasts through two MCP servers:

| Server | Method | Source |
|--------|--------|--------|
| `weather_USA.py` | HTTP API | National Weather Service (api.weather.gov) |
| `weather_Israel.py` | Browser automation | weather2day.co.il via **Playwright** |

---

## Architecture

```
host.py  (Claude + chat loop)
   ├── client.py → weather_USA.py    (MCP server, NWS API)
   └── client.py → weather_Israel.py (MCP server, Playwright)
```

`host.py` connects to both MCP servers, collects all their tools, and passes them to Claude. Claude decides which tool to call based on the user's question.

---

## Setup

### 1. Install dependencies
```bash
uv sync
```

### 2. Install Chromium for Playwright
```bash
uv run playwright install chromium
```

### 3. Set your Anthropic API key
```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# or add it to a .env file / your shell profile
```

### 4. Run
```bash
uv run host.py
```

---

## Israel Weather Tools (Playwright)

| Tool | Description |
|------|-------------|
| `open_weather_forecast_israel` | Opens Chromium and navigates to weather2day.co.il/forecast |
| `enter_weather_forecast_city_israel` | Types the city name into the search field |
| `select_weather_forecast_city_israel` | Clicks the first autocomplete result |
| `get_weather_forecast_content_israel` | Extracts the forecast text from the page (RAG) |

Claude calls these tools **in order** whenever you ask about Israeli weather. You will see a real browser open on your screen.

---

## USA Weather Tools (API)

| Tool | Description |
|------|-------------|
| `get_weather_usa` | Fetches the NWS forecast for a US city (no API key required) |

---

## Example Questions

```
What's the weather like in Tel Aviv today?
מה התחזית לירושלים?
What will the weather be in Chicago tomorrow?
תגיד לי מה מזג האוויר בחיפה?
Is it going to rain in Miami this week?
```

---

## Project Structure

```
.
├── pyproject.toml       # uv dependencies
├── client.py            # Generic MCP client (stdio)
├── host.py              # Claude chat loop + multi-MCP orchestration
├── weather_USA.py       # MCP Server — US cities via NWS API
└── weather_Israel.py    # MCP Server — Israeli cities via Playwright
```
