# Open-Meteo Weather Search

Open-Meteo API를 이용해 사용자가 입력한 위치의 오늘 시간별 날씨를 조회하고, Matplotlib로 기온 그래프를 생성하는 예제입니다.

## Local scripts

```powershell
.\.venv\Scripts\python.exe .\open_meteo_hourly_today.py
.\.venv\Scripts\python.exe .\plot_today_temperature.py
```

## Local web server

```powershell
.\.venv\Scripts\python.exe .\weather_web.py
```

## Vercel deployment

Vercel에서는 `public/index.html`이 웹 페이지를 제공하고, `api/weather.py`가 Python Function으로 Open-Meteo 조회와 Matplotlib 그래프 생성을 처리합니다.

필수 설정:

- Framework Preset: `Other`
- Build Command: 비워두기
- Output Directory: 비워두기
- Python version: `.python-version`의 `3.12`
