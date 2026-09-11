"""core 모듈에 대한 단위 테스트."""

from news_briefing.core import ProjectSettings, get_system_info


def test_project_settings_default() -> None:
    """ProjectSettings 기본값 유효성 검증."""
    settings = ProjectSettings()
    assert settings.app_name == "news-briefing"
    assert settings.app_env in ("development", "test", "production")
    assert isinstance(settings.debug, bool)
    assert settings.gemini_model == "gemini-2.5-flash"


def test_get_system_info() -> None:
    """시스템 정보 수집 기능 검증."""
    info = get_system_info()
    assert "python_version" in info
    # Python 3.12 런타임 확인
    assert info["python_version"].startswith("3.12")
    assert "django_version" in info
    assert info["django_version"] != "Not Installed"
    assert "google_genai_version" in info
    assert info["google_genai_version"] != "Not Installed"
    assert "is_venv" in info
    assert "workspace_dir" in info
