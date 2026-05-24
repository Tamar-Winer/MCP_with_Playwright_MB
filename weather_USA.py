import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Weather USA")

NWS_HEADERS = {"User-Agent": "WeatherMCP/1.0 (educational project, contact: student)"}

# Coordinates for common US cities
CITY_COORDS: dict[str, tuple[float, float]] = {
    "new york": (40.7128, -74.0060),
    "los angeles": (34.0522, -118.2437),
    "chicago": (41.8781, -87.6298),
    "houston": (29.7604, -95.3698),
    "phoenix": (33.4484, -112.0740),
    "philadelphia": (39.9526, -75.1652),
    "san antonio": (29.4241, -98.4936),
    "san diego": (32.7157, -117.1611),
    "dallas": (32.7767, -96.7970),
    "san francisco": (37.7749, -122.4194),
    "seattle": (47.6062, -122.3321),
    "denver": (39.7392, -104.9903),
    "boston": (42.3601, -71.0589),
    "miami": (25.7617, -80.1918),
    "atlanta": (33.7490, -84.3880),
    "minneapolis": (44.9778, -93.2650),
    "portland": (45.5051, -122.6750),
    "las vegas": (36.1699, -115.1398),
    "nashville": (36.1627, -86.7816),
    "new orleans": (29.9511, -90.0715),
    "austin": (30.2672, -97.7431),
    "washington": (38.9072, -77.0369),
    "detroit": (42.3314, -83.0458),
    "memphis": (35.1495, -90.0490),
    "baltimore": (39.2904, -76.6122),
}


@mcp.tool()
async def get_weather_usa(city: str) -> str:
    """Get the weather forecast for a US city using the National Weather Service API.

    Args:
        city: Name of the US city (e.g. "New York", "Los Angeles", "Chicago")
    """
    city_key = city.lower().strip()

    if city_key not in CITY_COORDS:
        available = ", ".join(sorted(CITY_COORDS.keys()))
        return (
            f"City '{city}' not found in the database.\n"
            f"Available cities: {available}"
        )

    lat, lon = CITY_COORDS[city_key]

    async with httpx.AsyncClient(headers=NWS_HEADERS, timeout=30) as client:
        # Step 1: resolve grid point
        points = await client.get(f"https://api.weather.gov/points/{lat},{lon}")
        points.raise_for_status()
        forecast_url = points.json()["properties"]["forecast"]

        # Step 2: fetch forecast
        forecast = await client.get(forecast_url)
        forecast.raise_for_status()
        periods = forecast.json()["properties"]["periods"][:4]

    lines = [f"Weather forecast for {city.title()}:\n"]
    for p in periods:
        lines.append(f"• {p['name']}")
        lines.append(f"  {p['temperature']}°{p['temperatureUnit']}  |  Wind: {p['windSpeed']} {p['windDirection']}")
        lines.append(f"  {p['detailedForecast']}\n")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
