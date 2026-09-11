# AI 뉴스 큐레이터 (AI News Curation App)

네이버 뉴스 검색 API와 Google 최신 **Gemini 2.5 Flash**를 결합하여, 사용자가 원하는 키워드와 필터링 조건에 부합하는 **핵심 기사 3개를 엄선 및 3줄 요약**해 주는 스마트 뉴스 브리핑 웹 애플리케이션입니다.

---

## 🌟 핵심 기능

1. **실시간 뉴스 검색**: 네이버 뉴스 오픈 API를 통해 입력된 키워드로 최신 20건의 뉴스 기사를 실시간 수집.
2. **AI 스마트 큐레이션**: 사용자가 제시한 '필터링 프롬프트' 기준에 따라 Gemini 2.5 AI가 기사 3건을 정밀 엄선.
3. **핵심 3줄 요약 & 시사점 도출**: 선정된 각 기사의 선정 이유, 3줄 핵심 요약, 그리고 인사이트 제공.
4. **프리미엄 Glassmorphism 웹 인터페이스**: 다크 모드 기반 세련된 카드 UI, 단계별 실시간 로딩 애니메이션, 수집된 20건 원본 기사 투명 검증 아코디언.
5. **CLI & Web 동시 지원**: 브라우저 UI뿐만 아니라 터미널 CLI에서도 한 줄 명령어로 즉시 큐레이션 가능.
6. **데모 시뮬레이션 지원**: API 키가 아직 없는 상태에서도 UI 인터랙션을 즉시 테스트할 수 있는 데모 프리뷰 모드 탑재.

---

## 🔑 환경 변수 (.env) 설정

프로젝트 루트의 `.env` 파일에 네이버 및 Gemini API 키를 입력합니다:

```ini
# Application Settings
APP_ENV=development
DEBUG=True

# Google Gemini API Settings (https://aistudio.google.com/)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Naver Search API Settings (https://developers.naver.com/apps/#/register)
NAVER_CLIENT_ID=your_naver_client_id_here
NAVER_CLIENT_SECRET=your_naver_client_secret_here
```

---

## 🚀 실행 가이드

> [!IMPORTANT]
> 본 프로젝트의 모든 Python/Django 작업은 워크스페이스 원칙에 따라 **`uv run`** 명령어를 사용합니다.

### 1. 웹 애플리케이션 실행
Django 개발 서버를 실행하고 브라우저에서 `http://127.0.0.1:8000`에 접속합니다:
```powershell
uv run python manage.py runserver
# 또는
.\dev.ps1 django manage.py runserver
```

### 2. 터미널 CLI 큐레이션 실행
웹 브라우저 없이 터미널에서 즉시 기사를 큐레이션할 수 있습니다:
```powershell
uv run news-briefing -k "인공지능 반도체" -f "국내 기업의 양산 및 수출 성과 위주"
```

### 3. 단위 테스트 및 코드 품질 점검
```powershell
# 단위 테스트 (11개 테스트)
uv run pytest -v

# 린트 & 포맷 & 타입 & 테스트 종합 무결성 검증
.\dev.ps1 check
```

---

## 🏗️ 아키텍처 구성

```
news-briefing/
├── config/                  # Django 메인 설정 및 루트 URL 라우팅
│   ├── settings.py
│   └── urls.py
├── curation/                # 뉴스 큐레이션 메인 앱
│   ├── services/            # 핵심 비즈니스 로직
│   │   ├── naver_service.py # 네이버 뉴스 검색 API 클라이언트 & HTML 정제
│   │   ├── gemini_service.py# Google Gemini 2.5 큐레이션 & 요약 엔진
│   │   ├── pipeline.py      # 수집-선별 통합 파이프라인 & 데모 생성
│   │   └── models.py        # Pydantic 도메인 모델
│   ├── templates/curation/  # Glassmorphism 반응형 HTML 템플릿
│   ├── static/curation/     # Vanilla CSS & 동적 비동기 인터랙션 JS
│   ├── views.py             # 대시보드 뷰 & 비동기 큐레이션 API
│   └── urls.py
├── src/news_briefing/       # 패키지 엔트리포인트 및 콘솔 CLI
├── tests/                   # pytest 단위/통합 테스트 스위트
├── dev.ps1                  # 개발 편의 PowerShell 런처
├── pyproject.toml           # uv 의존성 및 툴 설정
└── .env                     # API 키 및 환경 설정
```
