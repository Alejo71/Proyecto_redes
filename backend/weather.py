from __future__ import annotations

from typing import Any

import httpx

from .models import WeatherReport


def weather_description(code: int) -> str:
    if code == 0:
        return "Despejado"
    if code in {1, 2}:
        return "Parcialmente nublado"
    if code in {3, 45, 48}:
        return "Nublado"
    if code in {51, 53, 55, 56, 57}:
        return "Llovizna"
    if code in {61, 63, 65, 66, 67, 80, 81, 82}:
        return "Lluvia"
    if code in {71, 73, 75, 77, 85, 86}:
        return "Nieve"
    if code in {95, 96, 99}:
        return "Tormenta"
    return "Variable"


def fallback_weather(lat: float, lng: float) -> WeatherReport:
    seed = abs(int((lat * 1000) + (lng * 1000)))
    code = [0, 2, 3, 61, 63, 80, 95][seed % 7]
    temperature = round(18 + (lat % 6) - (abs(lng) % 3), 1)
    wind_speed = round(4 + (seed % 12) * 0.7, 1)
    precipitation = round((seed % 100) / 6, 1)

    return WeatherReport(
        temperature=temperature,
        wind_speed=wind_speed,
        precipitation=precipitation,
        weather_code=code,
        description=weather_description(code),
        source="simulado",
    )


async def get_weather_report(lat: float, lng: float) -> WeatherReport:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lng}&current=temperature_2m,precipitation,wind_speed_10m,weather_code"
        "&timezone=America%2FBogota"
    )

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            current = payload.get("current", {})
            code = int(current.get("weather_code", 0))

            return WeatherReport(
                temperature=float(current.get("temperature_2m", 0.0)),
                wind_speed=float(current.get("wind_speed_10m", 0.0)),
                precipitation=float(current.get("precipitation", 0.0)),
                weather_code=code,
                description=weather_description(code),
                source="open-meteo",
            )
    except Exception:
        return fallback_weather(lat, lng)