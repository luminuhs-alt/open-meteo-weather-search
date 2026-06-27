#!/usr/bin/env python3
"""Fetch today's hourly weather forecast from the Open-Meteo API."""

from __future__ import annotations

import argparse
import json
from datetime import date
from urllib.parse import urlencode
from urllib.request import urlopen


WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def fetch_hourly_weather(
    latitude: float,
    longitude: float,
    timezone: str,
    forecast_days: int = 1,
) -> dict:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(
            [
                "temperature_2m",
                "apparent_temperature",
                "relative_humidity_2m",
                "precipitation_probability",
                "precipitation",
                "weather_code",
                "wind_speed_10m",
            ]
        ),
        "forecast_days": forecast_days,
        "timezone": timezone,
    }
    url = f"https://api.open-meteo.com/v1/forecast?{urlencode(params)}"

    with urlopen(url, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def print_today_hourly_weather(data: dict) -> None:
    hourly = data["hourly"]
    units = data.get("hourly_units", {})
    today = date.today().isoformat()

    print(f"Hourly weather for {today}")
    print(
        "Time  | Temp | Feels | Humidity | Rain % | Precip | Wind | Weather"
    )
    print("-" * 78)

    for index, timestamp in enumerate(hourly["time"]):
        if not timestamp.startswith(today):
            continue

        code = hourly["weather_code"][index]
        weather = WEATHER_CODES.get(code, f"Code {code}")
        time_label = timestamp.split("T", maxsplit=1)[1]

        print(
            f"{time_label} | "
            f"{hourly['temperature_2m'][index]:>4} {units.get('temperature_2m', ''):<2} | "
            f"{hourly['apparent_temperature'][index]:>5} {units.get('apparent_temperature', ''):<2} | "
            f"{hourly['relative_humidity_2m'][index]:>7} {units.get('relative_humidity_2m', ''):<2} | "
            f"{hourly['precipitation_probability'][index]:>5} {units.get('precipitation_probability', ''):<1} | "
            f"{hourly['precipitation'][index]:>6} {units.get('precipitation', ''):<2} | "
            f"{hourly['wind_speed_10m'][index]:>4} {units.get('wind_speed_10m', ''):<4} | "
            f"{weather}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Get today's hourly weather from Open-Meteo."
    )
    parser.add_argument("--latitude", type=float, default=37.5665, help="Latitude")
    parser.add_argument("--longitude", type=float, default=126.9780, help="Longitude")
    parser.add_argument(
        "--timezone",
        default="Asia/Seoul",
        help='Timezone name, for example "Asia/Seoul" or "auto".',
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = fetch_hourly_weather(args.latitude, args.longitude, args.timezone)
    print_today_hourly_weather(data)


if __name__ == "__main__":
    main()
