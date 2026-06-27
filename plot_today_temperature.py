#!/usr/bin/env python3
"""Plot hourly temperature from Open-Meteo and save it as an image."""

from __future__ import annotations

import argparse
from io import BytesIO
from datetime import date, datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from open_meteo_hourly_today import fetch_hourly_weather


def get_temperature_series(data: dict, target_date: date) -> tuple[list[str], list[float]]:
    hourly = data["hourly"]
    all_times = [datetime.fromisoformat(value) for value in hourly["time"]]
    matching_indexes = [
        index for index, time in enumerate(all_times) if time.date() == target_date
    ]

    if not matching_indexes:
        raise ValueError(f"No hourly temperature data found for {target_date}")

    times = [all_times[index] for index in matching_indexes]
    temperatures = [hourly["temperature_2m"][index] for index in matching_indexes]
    labels = [time.strftime("%H:%M") for time in times]
    return labels, temperatures


def draw_temperature_chart(
    labels: list[str],
    temperatures: list[float],
    location_name: str,
    target_date: date,
) -> None:
    plt.figure(figsize=(12, 6))
    plt.plot(labels, temperatures, marker="o", linewidth=2, color="#2563eb")
    plt.fill_between(labels, temperatures, alpha=0.12, color="#2563eb")

    plt.title(f"Hourly Temperature on {target_date.isoformat()} - {location_name}")
    plt.xlabel("Time")
    plt.ylabel("Temperature (C)")
    plt.grid(True, linestyle="--", alpha=0.35)
    plt.xticks(rotation=45)
    plt.tight_layout()


def build_temperature_chart(
    data: dict,
    output_path: Path,
    location_name: str,
    target_date: date,
) -> None:
    labels, temperatures = get_temperature_series(data, target_date)
    draw_temperature_chart(labels, temperatures, location_name, target_date)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()


def build_temperature_chart_png(
    data: dict,
    location_name: str,
    target_date: date,
) -> bytes:
    labels, temperatures = get_temperature_series(data, target_date)
    draw_temperature_chart(labels, temperatures, location_name, target_date)
    buffer = BytesIO()
    plt.savefig(buffer, format="png", dpi=150)
    plt.close()
    buffer.seek(0)
    return buffer.read()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Save today's hourly temperature chart from Open-Meteo."
    )
    parser.add_argument("--latitude", type=float, default=37.5665, help="Latitude")
    parser.add_argument("--longitude", type=float, default=126.9780, help="Longitude")
    parser.add_argument(
        "--timezone",
        default="Asia/Seoul",
        help='Timezone name, for example "Asia/Seoul" or "auto".',
    )
    parser.add_argument("--location-name", default="Seoul", help="Chart location name")
    parser.add_argument(
        "--days-from-today",
        type=int,
        default=0,
        help="0 for today, 1 for tomorrow, and so on.",
    )
    parser.add_argument(
        "--output",
        default="today_temperature.png",
        help="Output image path",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target_date = date.today() + timedelta(days=args.days_from_today)
    forecast_days = max(args.days_from_today + 1, 1)
    data = fetch_hourly_weather(
        args.latitude,
        args.longitude,
        args.timezone,
        forecast_days=forecast_days,
    )
    output_path = Path(args.output)
    build_temperature_chart(data, output_path, args.location_name, target_date)
    print(f"Saved chart: {output_path.resolve()}")


if __name__ == "__main__":
    main()
