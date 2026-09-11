"""news-briefing CLI 엔트리포인트 및 콘솔 큐레이션 실행 모듈."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트를 sys.path에 등록하여 curation 모듈 로드 지원
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from curation.services.pipeline import run_curation_pipeline  # noqa: E402
from news_briefing.core import ProjectSettings, get_system_info  # noqa: E402

load_dotenv()


def reconfigure_console_utf8() -> None:
    """Windows 콘솔(CP949) 환경에서 UTF-8 인코딩 충돌을 방지합니다."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def run_cli_curation(keyword: str, filter_prompt: str) -> None:
    """터미널에서 직접 네이버 검색 및 Gemini 큐레이션을 실행하고 결과를 출력합니다."""
    print("=" * 65)
    print(f"🔍 [뉴스 큐레이션 검색] 키워드: '{keyword}'")
    print(f"🎯 [AI 필터링 기준]   : '{filter_prompt}'")
    print("=" * 65)
    print("⏳ 네이버 뉴스 20건을 수집하고 Gemini 2.5 AI로 분석 중입니다...\n")

    try:
        result = run_curation_pipeline(keyword, filter_prompt, allow_demo_fallback=True)

        if result.metadata.get("is_demo"):
            print("⚠️  [참고] API 키가 설정되지 않아 데모 시뮬레이션 모드로 실행되었습니다.")
            print("    실시간 뉴스를 가져오려면 .env 파일에 NAVER 및 GEMINI 키를 설정해주세요.\n")

        print("🎉 20건의 뉴스 중 필터 기준에 가장 부합하는 TOP 3 기사를 선정했습니다:\n")

        for idx, art in enumerate(result.curated_articles, 1):
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"★ [{idx}위] {art.title}")
            print(f"• 원본 기사 번호 : {art.article_index}번")
            print(f"• 기사 링크      : {art.link}")
            print(f"• AI 선정 이유   : {art.reason}")
            print("\n[핵심 3줄 요약]")
            for bullet in art.summary_bullets:
                print(f"  - {bullet}")
            print(f"\n[핵심 인사이트] {art.key_insight}")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    except Exception as exc:
        print(f"❌ 오류 발생: {exc}")


def print_banner() -> None:
    """프로젝트 환경 상태 및 명령어 안내 배너를 출력합니다."""
    settings = ProjectSettings.load_from_env()
    info = get_system_info()

    border = "=" * 65
    print(border)
    print(f"🚀  {settings.app_name} 개발 환경 및 AI 뉴스 큐레이터가 준비되었습니다.")
    print(border)
    print(f"• Python 버전      : {info['python_version']}")
    print(f"• 가상환경 활성화 : {'예 (.venv)' if info['is_venv'] else '아니오'}")
    print(f"• Django 버전      : {info.get('django_version', 'N/A')}")
    print(f"• Gemini SDK 버전  : {info.get('google_genai_version', 'N/A')}")
    print(f"• 기본 Gemini 모델 : {settings.gemini_model}")
    print(f"• Naver API 설정   : {'설정됨' if os.getenv('NAVER_CLIENT_ID') else '미설정'}")
    print(f"• Gemini API 설정  : {'설정됨' if os.getenv('GEMINI_API_KEY') else '미설정'}")
    print(border)
    print("💡 사용 방법 (항상 'uv run' 접두사 사용):")
    print("  1. 웹 대시보드 서버 실행: uv run python manage.py runserver")
    print("     또는 편의 런처 실행   : .\\dev.ps1 django manage.py runserver")
    print('  2. 콘솔 즉시 큐레이션   : uv run news-briefing -k "생성형 AI" -f "상용화 소식"')
    print("  3. 단위 테스트 실행     : uv run pytest")
    print("  4. 종합 코드 품질 점검  : .\\dev.ps1 check")
    print(border)


def main() -> None:
    """메인 엔트리포인트."""
    reconfigure_console_utf8()

    parser = argparse.ArgumentParser(description="AI 뉴스 큐레이터 CLI")
    parser.add_argument("-k", "--keyword", type=str, help="검색할 뉴스 키워드")
    parser.add_argument("-f", "--filter", type=str, help="기사 선별용 AI 필터링 프롬프트")
    parser.add_argument("--server", action="store_true", help="Django 개발 서버 실행")

    args = parser.parse_args()

    if args.server:
        print("🌐 Django 개발 서버를 시작합니다 (http://127.0.0.1:8000)...")
        subprocess.run([sys.executable, "manage.py", "runserver"])
        return

    if args.keyword and args.filter:
        run_cli_curation(args.keyword, args.filter)
    else:
        print_banner()


if __name__ == "__main__":
    main()
