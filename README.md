# News Briefing (뉴스 브리핑)

Django와 Google Gemini API를 활용한 맞춤형 AI 뉴스 브리핑 서비스 프로젝트입니다.
**Astral uv**를 통해 Python 3.12 환경 및 의존성을 관리합니다.

---

## 📌 주요 기술 스택 및 환경
- **Python**: 3.12 (CPython 3.12.14 고정)
- **패키지 및 가상환경 관리**: [Astral uv](https://github.com/astral-sh/uv)
- **웹 프레임워크**: Django 6.x
- **생성형 AI SDK**: `google-genai` (공식 Google Gemini API SDK)
- **데이터 모델링 & 설정**: `pydantic`, `python-dotenv`
- **코드 품질 도구**: `ruff` (Linter/Formatter), `mypy` (Type Checker), `pytest` / `pytest-django`

---

## ⚡ 핵심 실행 원칙: `uv run` 필수 사용

> [!IMPORTANT]
> 본 프로젝트에서는 시스템 파이썬을 직접 호출하지 않고, **항상 `uv run` 명령어를 통해 `.venv` 가상환경 내에서 파이썬과 도구를 실행**합니다.

```bash
# 올바른 실행 방식 (가상환경 자동 연동)
uv run python <스크립트.py>
uv run news-briefing
uv run pytest
uv run ruff check .

# 피해야 할 방식 (시스템 파이썬 직접 호출)
# python <스크립트.py>
```

---

## 🚀 빠른 시작 (Quick Start)

### 1. 환경 변수 설정
`.env.example` 파일을 복사하여 `.env`를 설정하고, Gemini API 키를 입력합니다.
```powershell
cp .env.example .env
```
`.env` 파일에 발급받은 Gemini API 키 입력:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. 가상환경 및 의존성 동기화
```powershell
uv sync
```

### 3. 프로젝트 초기 실행 및 상태 점검
```powershell
uv run news-briefing
```
또는 PowerShell 편의 런처 사용:
```powershell
.\dev.ps1 run
```

---

## 🛠️ 개발 명령어 가이드

편의 스크립트(`.\dev.ps1`) 또는 `uv run` 명령어를 통해 실행할 수 있습니다.

| 작업 | uv 명령어 | dev.ps1 편의 명령어 |
| :--- | :--- | :--- |
| **프로젝트 실행** | `uv run news-briefing` | `.\dev.ps1 run` |
| **단위 테스트** | `uv run pytest -v` | `.\dev.ps1 test` |
| **코드 린트** | `uv run ruff check .` | `.\dev.ps1 lint` |
| **코드 포맷팅** | `uv run ruff format .` | `.\dev.ps1 format` |
| **타입 검사** | `uv run mypy src` | `.\dev.ps1 typecheck` |
| **품질 종합 검증** | - | `.\dev.ps1 check` |
| **의존성 동기화** | `uv sync` | `.\dev.ps1 sync` |
| **패키지 추가** | `uv add <패키지명>` | - |
| **개발 패키지 추가**| `uv add --dev <패키지명>` | - |

---

## 🌐 Django 개발 가이드 (향후 진행 시)

Django 앱 생성 또는 마이그레이션, 서버 실행 시에도 `uv run`을 사용합니다:
```powershell
# Django 프로젝트 시작 (필요 시)
uv run django-admin startproject config .

# 데이터베이스 마이그레이션
uv run python manage.py migrate

# 개발 서버 실행
uv run python manage.py runserver
# 또는
.\dev.ps1 django manage.py runserver
```

---

## 🤖 Google Gemini API 사용 예시

```python
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

# 클라이언트 초기화 (GEMINI_API_KEY 환경변수 자동 인식)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content(
    model="gemini-2.5-flash", contents="오늘의 주요 IT 뉴스를 한 줄로 요약해줘."
)
print(response.text)
```
