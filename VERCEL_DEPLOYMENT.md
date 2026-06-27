# Vercel 배포 설정 정리

이 프로젝트는 현재 `weather_web.py`로 로컬 웹 서버를 실행하는 구조입니다. Vercel에서는 계속 실행되는 서버 프로세스 대신 Python Function 형태로 배포해야 하므로, 배포 전 구조를 아래처럼 맞추는 것을 권장합니다.

## 권장 파일 구조

```text
.
├─ api/
│  └─ index.py
├─ public/
│  └─ index.html
├─ open_meteo_hourly_today.py
├─ plot_today_temperature.py
├─ requirements.txt
├─ vercel.json
└─ .python-version
```

## Vercel 프로젝트 설정

| 항목 | 지정값 |
| --- | --- |
| Framework Preset | Other |
| Root Directory | `.` |
| Build Command | 비워두기 |
| Output Directory | 비워두기 |
| Install Command | 기본값 사용 또는 `pip install -r requirements.txt` |
| Development Command | 로컬에서만 필요하면 비워두기 |
| Environment Variables | 현재는 필요 없음 |

## Python 버전

Vercel Python Runtime은 Python 버전을 `.python-version`, `pyproject.toml`, `Pipfile.lock` 등으로 지정할 수 있습니다. 이 프로젝트는 아래처럼 두는 것을 권장합니다.

```text
3.12
```

파일명:

```text
.python-version
```

## requirements.txt

현재 그래프 생성에 Matplotlib를 사용하므로, 최소 의존성은 아래와 같습니다.

```text
matplotlib
```

Python 서버리스 함수에서 이미지 대신 JSON 데이터를 내려주고 브라우저에서 Chart.js 등으로 그리도록 바꾸면 Matplotlib 의존성을 제거할 수 있습니다. 다만 “지금 만든 파이썬 코드로 시각화”를 유지하려면 Matplotlib를 포함합니다.

## vercel.json 예시

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "functions": {
    "api/**/*.py": {
      "maxDuration": 30,
      "excludeFiles": "{.venv/**,__pycache__/**,static/**,*.png}"
    }
  },
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/api/$1"
    },
    {
      "source": "/(.*)",
      "destination": "/public/index.html"
    }
  ]
}
```

## API 엔트리포인트

Vercel의 Python Function은 `api/index.py` 같은 `/api` 폴더 안의 Python 파일을 함수로 인식할 수 있습니다. 이 파일은 `BaseHTTPRequestHandler`를 상속한 `handler` 또는 ASGI/WSGI `app`을 노출해야 합니다.

권장 방식:

```text
api/index.py
```

역할:

- 사용자 입력 위치를 쿼리스트링으로 받기
- Open-Meteo geocoding API로 좌표 조회
- `open_meteo_hourly_today.py`의 `fetch_hourly_weather()` 호출
- `plot_today_temperature.py`의 그래프 생성 로직을 사용하거나, 시간별 기온 데이터를 JSON으로 반환

## 주의할 점

- `weather_web.py`의 `ThreadingHTTPServer`는 로컬 실행용입니다. Vercel 배포용으로는 `api/index.py` 형태로 옮겨야 합니다.
- Vercel 함수 환경의 파일 시스템은 영구 저장소가 아닙니다. 요청 때마다 PNG를 서버에 저장해서 재사용하는 방식보다, 이미지 응답을 바로 반환하거나 JSON 데이터를 프론트엔드에서 그래프로 그리는 방식이 안정적입니다.
- `.venv`, `__pycache__`, 생성된 PNG 파일은 Git/Vercel 배포 대상에서 제외하는 것이 좋습니다.
- Open-Meteo는 별도 API 키가 필요 없으므로 환경 변수는 현재 필요 없습니다.

## 배포 전 체크리스트

- [ ] `requirements.txt` 추가
- [ ] `.python-version` 추가
- [ ] `api/index.py`로 Vercel Function 작성
- [ ] `public/index.html`에서 위치 입력 UI 작성
- [ ] `vercel.json` 추가
- [ ] `.venv`, `__pycache__`, `*.png` 배포 제외
- [ ] 로컬에서 `vercel dev`로 동작 확인
- [ ] Vercel 프로젝트 설정에서 Framework Preset을 `Other`로 지정

## 참고 문서

- [Vercel Python Runtime](https://vercel.com/docs/functions/runtimes/python)
- [Vercel Project Configuration](https://vercel.com/docs/project-configuration)
