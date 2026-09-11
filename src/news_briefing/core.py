"""핵심 설정 및 시스템 상태 모듈."""

import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# 환경 변수 로드 (.env)
load_dotenv()


class ProjectSettings(BaseModel):
    """프로젝트 기본 환경 설정 모델."""

    app_name: str = Field(default="news-briefing", description="애플리케이션 명칭")
    app_env: str = Field(default="development", description="실행 환경")
    debug: bool = Field(default=True, description="디버그 모드")
    log_level: str = Field(default="INFO", description="로그 레벨")
    gemini_api_key: str = Field(default="", description="Google Gemini API 키")
    gemini_model: str = Field(default="gemini-2.5-flash", description="기본 Gemini 모델명")

    @classmethod
    def load_from_env(cls) -> "ProjectSettings":
        """환경 변수로부터 설정을 로드합니다."""
        return cls(
            app_name=os.getenv("APP_NAME", "news-briefing"),
            app_env=os.getenv("APP_ENV", "development"),
            debug=os.getenv("DEBUG", "True").lower() in ("true", "1", "t"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        )


def get_system_info() -> dict[str, Any]:
    """현재 Python 런타임 및 주요 패키지 버전 정보를 수집합니다."""
    info: dict[str, Any] = {
        "python_version": sys.version.split()[0],
        "python_executable": sys.executable,
        "is_venv": sys.prefix != getattr(sys, "base_prefix", sys.prefix),
        "venv_path": sys.prefix,
        "workspace_dir": str(Path.cwd()),
    }

    try:
        import django

        info["django_version"] = django.get_version()
    except ImportError:
        info["django_version"] = "Not Installed"

    try:
        import google.genai

        info["google_genai_version"] = getattr(google.genai, "__version__", "Installed")
    except ImportError:
        info["google_genai_version"] = "Not Installed"

    return info
