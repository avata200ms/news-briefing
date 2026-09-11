"""news-briefing CLI 엔트리포인트 모듈."""

import sys

from news_briefing.core import ProjectSettings, get_system_info


def reconfigure_console_utf8() -> None:
    """Windows 콘솔(CP949) 환경에서 UTF-8 인코딩 충돌을 방지합니다."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    """메인 실행 함수."""
    reconfigure_console_utf8()

    settings = ProjectSettings.load_from_env()
    info = get_system_info()

    border = "=" * 60
    print(border)
    print(f"🚀  {settings.app_name} 개발 환경이 준비되었습니다.")
    print(border)
    print(f"• Python 버전      : {info['python_version']}")
    print(f"• 인터프리터 경로 : {info['python_executable']}")
    print(f"• 가상환경 활성화 : {'예 (.venv)' if info['is_venv'] else '아니오'}")
    print(f"• 가상환경 경로   : {info['venv_path']}")
    print(f"• Django 버전      : {info.get('django_version', 'N/A')}")
    print(f"• Gemini SDK 버전  : {info.get('google_genai_version', 'N/A')}")
    print(f"• 기본 Gemini 모델 : {settings.gemini_model}")
    print(border)
    print("💡 개발 및 실행 명령어 (항상 'uv run' 접두사 사용):")
    print("  1. 프로젝트 실행  : uv run news-briefing")
    print("  2. 테스트 실행    : uv run pytest")
    print("  3. 코드 린트      : uv run ruff check .")
    print("  4. 코드 포맷팅    : uv run ruff format .")
    print("  5. 타입 검사      : uv run mypy src")
    print("  6. 패키지 동기화  : uv sync")
    print("  7. 편의 런처      : .\\dev.ps1 run | test | lint | check")
    print(border)


if __name__ == "__main__":
    main()
