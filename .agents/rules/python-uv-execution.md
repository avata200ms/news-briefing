---
description: 이 프로젝트에서 Python 실행 시 항상 uv run 가상환경 명령어를 사용하도록 강제하는 규칙
---

# Python Execution Rule for News Briefing Project

- **원칙**: 이 프로젝트에서 Python 스크립트, 테스트, 린터, 프레임워크 명령(예: Django manage.py 등)을 실행할 때는 시스템 파이썬(`python ...`)을 직접 호출하지 않고 **반드시 `uv run`** 접두사를 사용해야 합니다.
- **실행 예시**:
  - Python 스크립트 실행: `uv run python <파일명.py>`
  - Django 관리 명령어: `uv run python manage.py runserver`, `uv run python manage.py migrate` 등
  - 테스트: `uv run pytest`
  - 린트 및 포맷: `uv run ruff check .`, `uv run ruff format .`
  - 타입 검사: `uv run mypy src`
  - 패키지 동기화: `uv sync`
  - 패키지 추가: `uv add <패키지>`, 개발용: `uv add --dev <패키지>`
