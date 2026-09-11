"""뉴스 큐레이션 웹 뷰 및 비동기 API 엔드포인트."""

import json
import os
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from curation.services.gemini_service import GeminiCurationError
from curation.services.naver_service import MissingAPIKeyError, NaverAPIError
from curation.services.pipeline import run_curation_pipeline


@ensure_csrf_cookie
@require_GET
def index(request: HttpRequest) -> HttpResponse:
    """메인 대시보드 뷰."""
    has_naver_id = bool(os.getenv("NAVER_CLIENT_ID", "").strip())
    has_naver_secret = bool(os.getenv("NAVER_CLIENT_SECRET", "").strip())
    has_gemini = bool(os.getenv("GEMINI_API_KEY", "").strip())

    context: dict[str, Any] = {
        "has_naver_keys": has_naver_id and has_naver_secret,
        "has_gemini_key": has_gemini,
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        "all_keys_ready": has_naver_id and has_naver_secret and has_gemini,
    }
    return render(request, "curation/index.html", context)


@require_POST
def curate_api(request: HttpRequest) -> JsonResponse:
    """사용자의 키워드와 필터링 프롬프트를 접수하여 네이버 검색 및 Gemini 큐레이션을 실행하는 API."""
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse(
            {"status": "error", "message": "잘못된 JSON 요청 형식입니다."},
            status=400,
        )

    keyword = body.get("keyword", "").strip()
    filter_prompt = body.get("filter_prompt", "").strip()
    allow_demo = body.get("allow_demo", True)  # 키 미입력 시 데모 허용 여부

    if not keyword:
        return JsonResponse(
            {"status": "error", "message": "검색 키워드를 입력해 주세요."},
            status=400,
        )
    if not filter_prompt:
        return JsonResponse(
            {"status": "error", "message": "기사를 선별할 필터링 프롬프트를 입력해 주세요."},
            status=400,
        )

    try:
        result = run_curation_pipeline(
            keyword=keyword,
            filter_prompt=filter_prompt,
            allow_demo_fallback=allow_demo,
        )
        return JsonResponse(
            {
                "status": "success",
                "data": result.model_dump(),
            }
        )

    except MissingAPIKeyError as exc:
        return JsonResponse(
            {
                "status": "error",
                "code": "MISSING_API_KEY",
                "message": str(exc),
            },
            status=400,
        )
    except (NaverAPIError, GeminiCurationError) as exc:
        return JsonResponse(
            {
                "status": "error",
                "code": "API_ERROR",
                "message": str(exc),
            },
            status=502,
        )
    except Exception as exc:
        return JsonResponse(
            {
                "status": "error",
                "code": "SERVER_ERROR",
                "message": f"서버 내부 오류가 발생했습니다: {exc}",
            },
            status=500,
        )
