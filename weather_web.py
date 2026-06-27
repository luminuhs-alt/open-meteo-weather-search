#!/usr/bin/env python3
"""Local weather search web page powered by Open-Meteo."""

from __future__ import annotations

import html
import json
import re
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse
from urllib.request import urlopen

from open_meteo_hourly_today import WEATHER_CODES, fetch_hourly_weather
from plot_today_temperature import build_temperature_chart


HOST = "127.0.0.1"
PORT = 8000
STATIC_DIR = Path("static")
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


def make_chart_filename(location_label: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", location_label).strip("_").lower()
    return f"temperature_{slug or 'location'}.png"


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


def render_page(
    query: str = "",
    location_label: str | None = None,
    chart_url: str | None = None,
    rows: list[dict] | None = None,
    error: str | None = None,
) -> str:
    escaped_query = html.escape(query)
    result_html = ""

    if error:
        result_html = f'<p class="message error">{html.escape(error)}</p>'
    elif location_label and chart_url and rows:
        table_rows = "\n".join(
            f"""
            <tr>
                <td>{html.escape(row["time"])}</td>
                <td>{row["temperature"]} &deg;C</td>
                <td>{row["feels_like"]} &deg;C</td>
                <td>{row["humidity"]}%</td>
                <td>{row["rain_probability"]}%</td>
                <td>{row["precipitation"]} mm</td>
                <td>{row["wind"]} km/h</td>
                <td>{html.escape(row["weather"])}</td>
            </tr>
            """
            for row in rows
        )
        result_html = f"""
        <section class="results">
            <div class="result-header">
                <div>
                    <p class="eyebrow">Open-Meteo forecast</p>
                    <h2>{html.escape(location_label)} 오늘의 시간별 기온</h2>
                </div>
                <span class="pill">{len(rows)} hourly points</span>
            </div>
            <img class="chart" src="{html.escape(chart_url)}" alt="Hourly temperature chart">
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>시간</th>
                            <th>기온</th>
                            <th>체감</th>
                            <th>습도</th>
                            <th>강수확률</th>
                            <th>강수량</th>
                            <th>풍속</th>
                            <th>날씨</th>
                        </tr>
                    </thead>
                    <tbody>{table_rows}</tbody>
                </table>
            </div>
        </section>
        """
    else:
        result_html = """
        <p class="message">
            도시나 지역명을 입력하면 오늘 1시간 간격 기온 그래프를 바로 보여줍니다.
        </p>
        """

    return f"""<!doctype html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>날씨 검색</title>
    <style>
        :root {{
            color-scheme: light;
            font-family: Arial, "Malgun Gothic", sans-serif;
            background: #f7f9fc;
            color: #172033;
        }}
        body {{
            margin: 0;
        }}
        main {{
            width: min(1120px, calc(100% - 32px));
            margin: 0 auto;
            padding: 40px 0;
        }}
        .top {{
            margin-bottom: 24px;
        }}
        h1 {{
            margin: 0 0 10px;
            font-size: clamp(30px, 5vw, 48px);
            line-height: 1.05;
        }}
        .subtitle {{
            margin: 0;
            color: #56647a;
            font-size: 17px;
        }}
        form {{
            display: flex;
            gap: 10px;
            align-items: center;
            margin: 24px 0 18px;
        }}
        input {{
            flex: 1;
            min-width: 0;
            height: 46px;
            border: 1px solid #cfd8e3;
            border-radius: 8px;
            padding: 0 14px;
            font-size: 16px;
        }}
        button {{
            height: 46px;
            border: 0;
            border-radius: 8px;
            background: #2563eb;
            color: white;
            padding: 0 18px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
        }}
        .message {{
            border: 1px solid #d7e0ec;
            border-radius: 8px;
            background: white;
            padding: 18px;
            color: #56647a;
        }}
        .error {{
            border-color: #f2b8b5;
            color: #a12a2a;
        }}
        .results {{
            background: white;
            border: 1px solid #d7e0ec;
            border-radius: 8px;
            padding: 22px;
        }}
        .result-header {{
            display: flex;
            justify-content: space-between;
            gap: 16px;
            align-items: start;
            margin-bottom: 18px;
        }}
        .eyebrow {{
            margin: 0 0 4px;
            color: #2563eb;
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
        }}
        h2 {{
            margin: 0;
            font-size: 24px;
        }}
        .pill {{
            border-radius: 999px;
            background: #eaf1ff;
            color: #1d4ed8;
            padding: 7px 12px;
            font-size: 13px;
            font-weight: 700;
            white-space: nowrap;
        }}
        .chart {{
            display: block;
            width: 100%;
            height: auto;
            border: 1px solid #e4eaf2;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .table-wrap {{
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th, td {{
            border-bottom: 1px solid #e6ecf3;
            padding: 10px 9px;
            text-align: left;
            white-space: nowrap;
        }}
        th {{
            color: #56647a;
            background: #f8fafc;
        }}
        @media (max-width: 640px) {{
            main {{
                width: min(100% - 20px, 1120px);
                padding-top: 24px;
            }}
            form {{
                flex-direction: column;
            }}
            input, button {{
                width: 100%;
            }}
            .results {{
                padding: 14px;
            }}
            .result-header {{
                display: block;
            }}
            .pill {{
                display: inline-block;
                margin-top: 12px;
            }}
        }}
    </style>
</head>
<body>
    <main>
        <section class="top">
            <h1>날씨 검색</h1>
            <p class="subtitle">위치를 입력하면 오늘 날씨를 불러오고 시간별 기온 그래프를 생성합니다.</p>
            <form action="/weather" method="get">
                <input name="location" value="{escaped_query}" placeholder="예: Seoul, Busan, New York" required>
                <button type="submit">검색</button>
            </form>
        </section>
        {result_html}
    </main>
</body>
</html>"""


class WeatherHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)

        if parsed_url.path == "/":
            self.send_html(render_page())
            return

        if parsed_url.path == "/weather":
            self.handle_weather(parsed_url.query)
            return

        if parsed_url.path.startswith("/static/"):
            self.serve_static(parsed_url.path)
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def handle_weather(self, query_string: str) -> None:
        query = parse_qs(query_string).get("location", [""])[0].strip()
        if not query:
            self.send_html(render_page(error="검색할 위치를 입력해주세요."))
            return

        try:
            location = search_location(query)
            location_label = make_location_label(location)
            timezone = location.get("timezone") or "auto"
            data = fetch_hourly_weather(
                location["latitude"],
                location["longitude"],
                timezone,
                forecast_days=1,
            )
            first_time = datetime.fromisoformat(data["hourly"]["time"][0])
            target_date = first_time.date()
            rows = build_hourly_rows(data, target_date)
            chart_filename = make_chart_filename(location_label)
            chart_path = STATIC_DIR / chart_filename
            build_temperature_chart(data, chart_path, location_label, target_date)
            chart_url = f"/static/{quote(chart_filename)}?v={int(datetime.now().timestamp())}"
            page = render_page(query, location_label, chart_url, rows)
        except Exception as exc:
            page = render_page(query, error=f"날씨를 불러오지 못했습니다: {exc}")

        self.send_html(page)

    def serve_static(self, request_path: str) -> None:
        filename = unquote(request_path.removeprefix("/static/"))
        file_path = (STATIC_DIR / filename).resolve()
        static_root = STATIC_DIR.resolve()

        if static_root not in file_path.parents or not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "image/png")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(file_path.read_bytes())

    def send_html(self, content: str) -> None:
        encoded = content.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> None:
    STATIC_DIR.mkdir(exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), WeatherHandler)
    print(f"Weather web page running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
