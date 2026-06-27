from __future__ import annotations

import base64
import json
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import urlopen

from open_meteo_hourly_today import WEATHER_CODES, fetch_hourly_weather
from plot_today_temperature import build_temperature_chart_png


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


def search_location(location_name: str) -> dict:
    params = {
        "name": location_name,
        "count": 1,
        "language": "en",
        "format": "json",
    }
    url = f"{GEOCODING_URL}?{urlencode(params)}"

    with urlopen(url, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))

    results = data.get("results", [])
    if not results:
        raise ValueError(f"No location found for {location_name!r}")

    return results[0]


def make_location_label(location: dict) -> str:
    parts = [
        location.get("name"),
        location.get("admin1"),
        location.get("country"),
    ]
    return ", ".join(part for part in parts if part)


def build_hourly_rows(data: dict, target_date) -> list[dict]:
    hourly = data["hourly"]
    rows = []

    for index, timestamp in enumerate(hourly["time"]):
        time_value = datetime.fromisoformat(timestamp)
        if time_value.date() != target_date:
            continue

        weather_code = hourly["weather_code"][index]
        rows.append(
            {
                "time": time_value.strftime("%H:%M"),
                "temperature": hourly["temperature_2m"][index],
                "feels_like": hourly["apparent_temperature"][index],
                "humidity": hourly["relative_humidity_2m"][index],
                "rain_probability": hourly["precipitation_probability"][index],
                "precipitation": hourly["precipitation"][index],
                "wind": hourly["wind_speed_10m"][index],
                "weather": WEATHER_CODES.get(weather_code, f"Code {weather_code}"),
            }
        )

    return rows


def weather_payload(location_query: str) -> dict:
    location = search_location(location_query)
    location_label = make_location_label(location)
    timezone = location.get("timezone") or "auto"
    data = fetch_hourly_weather(
        location["latitude"],
        location["longitude"],
        timezone,
        forecast_days=1,
    )
    target_date = datetime.fromisoformat(data["hourly"]["time"][0]).date()
    chart_png = build_temperature_chart_png(data, location_label, target_date)
    chart_base64 = base64.b64encode(chart_png).decode("ascii")

    return {
        "location": location_label,
        "date": target_date.isoformat(),
        "chart": f"data:image/png;base64,{chart_base64}",
        "rows": build_hourly_rows(data, target_date),
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        location = parse_qs(parsed_url.query).get("location", [""])[0].strip()

        if not location:
            self.send_json(
                {"error": "location query parameter is required"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        try:
            payload = weather_payload(location)
            self.send_json(payload)
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_GATEWAY)

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
