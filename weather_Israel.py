"""
Israel Weather MCP Server
Uses Playwright to control a real browser and scrape weather2day.co.il
"""
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page, Playwright
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Weather Israel")

WEATHER_URL = "https://www.weather2day.co.il/forecast"

# Module-level browser state — persists across tool calls within one server process
_playwright: Optional[Playwright] = None
_browser: Optional[Browser] = None
_page: Optional[Page] = None


# ─── Tool 1 ────────────────────────────────────────────────────────────────────

@mcp.tool()
async def open_weather_forecast_israel() -> str:
    """
    Opens a Chromium browser and navigates to the Israeli weather forecast site
    (weather2day.co.il/forecast).
    Must be called before any other Israel weather tool.
    """
    global _playwright, _browser, _page

    # Close any previously opened browser
    if _browser:
        await _browser.close()
    if _playwright:
        await _playwright.stop()

    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(headless=False, slow_mo=300)
    context = await _browser.new_context(
        locale="he-IL",
        viewport={"width": 1280, "height": 800},
    )
    _page = await context.new_page()

    await _page.goto(WEATHER_URL, wait_until="domcontentloaded")
    await _page.wait_for_timeout(2500)  # Let JS render

    title = await _page.title()
    return f"Browser opened and navigated to {WEATHER_URL}\nPage title: {title}"


# ─── Tool 2 ────────────────────────────────────────────────────────────────────

@mcp.tool()
async def enter_weather_forecast_city_israel(city: str) -> str:
    """
    Types a city name into the search field on the Israeli weather site.
    Must be called after open_weather_forecast_israel.

    Args:
        city: City name in Hebrew or English, e.g. "תל אביב", "ירושלים", "חיפה", "Tel Aviv"
    """
    global _page

    if _page is None:
        return "Error: browser is not open. Call open_weather_forecast_israel first."

    # Ordered list of selectors to try — most specific first
    search_selectors = [
        "input[type='search']",
        "input[role='combobox']",
        "[class*='search' i] input",
        "[class*='Search'] input",
        "[id*='search' i] input",
        "input[placeholder*='חיפ']",
        "input[placeholder*='עיר']",
        "input[placeholder*='מיקום']",
        "input[placeholder*='earch']",
        "input[placeholder*='city']",
        "header input[type='text']",
        "nav input[type='text']",
        "form input[type='text']",
    ]

    for selector in search_selectors:
        try:
            el = _page.locator(selector).first
            if await el.count() > 0 and await el.is_visible():
                await el.click()
                await el.fill(city)
                await _page.wait_for_timeout(1800)
                return f"Entered '{city}' in the search field. Waiting for autocomplete…"
        except Exception:
            continue

    # Fallback: click any visible text input that is not a login/email field
    try:
        inputs = _page.locator(
            "input[type='text']:not([autocomplete='email']):not([name*='email']):not([name*='pass'])"
        )
        count = await inputs.count()
        for i in range(count):
            el = inputs.nth(i)
            if await el.is_visible():
                await el.click()
                await el.fill(city)
                await _page.wait_for_timeout(1800)
                return f"Entered '{city}' in a text input field (fallback). Waiting for autocomplete…"
    except Exception:
        pass

    return (
        "Could not find a search input on the page. "
        "The site may load it dynamically — try increasing wait time or check the browser."
    )


# ─── Tool 3 ────────────────────────────────────────────────────────────────────

@mcp.tool()
async def select_weather_forecast_city_israel() -> str:
    """
    Selects the first city suggestion from the autocomplete dropdown.
    Must be called after enter_weather_forecast_city_israel.
    Waits for the forecast page to load and returns the current URL.
    """
    global _page

    if _page is None:
        return "Error: browser is not open. Call open_weather_forecast_israel first."

    dropdown_selectors = [
        "[role='option']:first-child",
        "[role='listbox'] [role='option']:first-child",
        "[role='listbox'] li:first-child",
        "[class*='autocomplete' i] li:first-child",
        "[class*='autocomplete' i] [class*='item']:first-child",
        "[class*='suggest' i] li:first-child",
        "[class*='result' i] li:first-child",
        "[class*='dropdown' i] li:first-child",
        "ul[class*='list' i] li:first-child",
        ".ui-autocomplete li:first-child",
        ".pac-item:first-child",
    ]

    for selector in dropdown_selectors:
        try:
            el = _page.locator(selector).first
            if await el.count() > 0 and await el.is_visible():
                await el.click()
                await _page.wait_for_load_state("domcontentloaded")
                await _page.wait_for_timeout(2000)
                current_url = _page.url
                title = await _page.title()
                return (
                    f"City selected from dropdown!\n"
                    f"URL: {current_url}\n"
                    f"Title: {title}"
                )
        except Exception:
            continue

    return (
        "Could not find the autocomplete dropdown. "
        "Possible causes: the city was not recognised, or the dropdown uses a selector not in our list. "
        "Check the open browser window."
    )


# ─── Tool 4 (Stage B) ──────────────────────────────────────────────────────────

@mcp.tool()
async def get_weather_forecast_content_israel() -> str:
    """
    Extracts and cleans the weather forecast text from the currently open browser page.
    Use this to read the forecast data and answer the user's question.
    Must be called after select_weather_forecast_city_israel.
    """
    global _page

    if _page is None:
        return "Error: browser is not open. Call open_weather_forecast_israel first."

    try:
        # Prefer focused content blocks over the full body
        content_selectors = [
            "[class*='forecast' i]",
            "[class*='weather' i]",
            "main",
            "article",
            "#content",
            ".content",
        ]

        raw = ""
        for selector in content_selectors:
            try:
                el = _page.locator(selector).first
                if await el.count() > 0:
                    candidate = await el.inner_text()
                    if len(candidate) > 200:
                        raw = candidate
                        break
            except Exception:
                continue

        if not raw:
            raw = await _page.inner_text("body")

        # Clean up
        noise = {
            "facebook", "twitter", "instagram", "youtube", "tiktok",
            "cookie", "cookies", "privacy", "copyright", "©",
            "newsletter", "subscribe", "advertisement",
        }
        lines = []
        for line in raw.splitlines():
            stripped = line.strip()
            if not stripped or len(stripped) < 2:
                continue
            if any(kw in stripped.lower() for kw in noise):
                continue
            lines.append(stripped)

        # Avoid sending more than ~150 lines to keep the context manageable
        content = "\n".join(lines[:150])
        url = _page.url

        return f"=== Weather Forecast Content ===\nSource: {url}\n\n{content}"

    except Exception as e:
        return f"Error extracting page content: {e}"


if __name__ == "__main__":
    mcp.run()
