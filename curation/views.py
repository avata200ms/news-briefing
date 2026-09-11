"""뉴스 큐레이션 웹 뷰 및 비동기 API 엔드포인트."""

import json
import os
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from curation.models import SavedSummary
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


@require_POST
def save_summary_api(request: HttpRequest) -> JsonResponse:
    """AI 요약 결과를 데이터베이스에 저장하는 API."""
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse(
            {"status": "error", "message": "잘못된 JSON 요청 형식입니다."},
            status=400,
        )

    # 복수 건(일괄) 저장 지원
    items = body.get("items")
    if isinstance(items, list) and items:
        saved_ids: list[int] = []
        default_keyword = body.get("keyword", "")
        for it in items:
            title = it.get("title", "").strip()
            summary_raw = it.get("summary") or it.get("summary_bullets") or ""
            if isinstance(summary_raw, list):
                summary = "\n".join(str(s) for s in summary_raw)
            else:
                summary = str(summary_raw).strip()

            if title and summary:
                record = SavedSummary.objects.create(
                    title=title,
                    summary=summary,
                    link=it.get("link", "").strip(),
                    reason=it.get("reason", "").strip(),
                    insight=it.get("key_insight") or it.get("insight", "").strip(),
                    keyword=it.get("keyword") or default_keyword,
                )
                saved_ids.append(record.id)

        return JsonResponse(
            {
                "status": "success",
                "message": f"{len(saved_ids)}건의 요약 결과가 저장되었습니다.",
                "saved_ids": saved_ids,
            }
        )

    # 단건 저장
    title = body.get("title", "").strip()
    summary_raw = body.get("summary") or body.get("summary_bullets") or ""
    if isinstance(summary_raw, list):
        summary = "\n".join(str(s) for s in summary_raw)
    else:
        summary = str(summary_raw).strip()

    if not title:
        return JsonResponse(
            {"status": "error", "message": "기사 제목이 필요합니다."},
            status=400,
        )
    if not summary:
        return JsonResponse(
            {"status": "error", "message": "요약 본문 내용이 필요합니다."},
            status=400,
        )

    record = SavedSummary.objects.create(
        title=title,
        summary=summary,
        link=body.get("link", "").strip(),
        reason=body.get("reason", "").strip(),
        insight=body.get("key_insight") or body.get("insight", "").strip(),
        keyword=body.get("keyword", "").strip(),
    )

    return JsonResponse(
        {
            "status": "success",
            "message": "기사 요약이 성공적으로 저장되었습니다.",
            "saved_id": record.id,
        }
    )


@ensure_csrf_cookie
@require_GET
def history_view(request: HttpRequest) -> HttpResponse:
    """사용자가 저장한 뉴스 요약 히스토리 페이지 뷰."""
    summaries = SavedSummary.objects.all()
    context: dict[str, Any] = {
        "summaries": summaries,
        "total_count": summaries.count(),
    }
    return render(request, "curation/history.html", context)


@require_POST
def delete_summary_api(request: HttpRequest, item_id: int) -> JsonResponse:
    """저장된 뉴스 요약 항목을 삭제하는 API."""
    try:
        record = SavedSummary.objects.get(id=item_id)
        record.delete()
        return JsonResponse({"status": "success", "message": "항목이 정상적으로 삭제되었습니다."})
    except SavedSummary.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "해당 요약 항목을 찾을 수 없습니다."},
            status=404,
        )
