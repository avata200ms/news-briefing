"""뉴스 큐레이션 웹 뷰 및 비동기 API 엔드포인트."""

import json
import os
from typing import Any

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from curation.models import SavedSummary
from curation.services.gemini_service import GeminiCurationError
from curation.services.naver_service import MissingAPIKeyError, NaverAPIError
from curation.services.pipeline import run_curation_pipeline


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    """사용자 로그인 뷰."""
    if request.user.is_authenticated:
        return redirect("curation:index")

    error_message = ""
    next_url = request.GET.get("next") or request.POST.get("next") or "/"

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            error_message = "아이디와 비밀번호를 모두 입력해 주세요."
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect(next_url)
            else:
                error_message = "아이디 또는 비밀번호가 올바르지 않습니다."

    return render(
        request,
        "curation/login.html",
        {"error_message": error_message, "next_url": next_url},
    )


@require_http_methods(["GET", "POST"])
def signup_view(request: HttpRequest) -> HttpResponse:
    """신규 사용자 회원가입 뷰."""
    if request.user.is_authenticated:
        return redirect("curation:index")

    error_message = ""

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        if not username or not password:
            error_message = "모든 필수 입력값을 입력해 주세요."
        elif len(username) < 3:
            error_message = "아이디는 최소 3자 이상이어야 합니다."
        elif len(password) < 4:
            error_message = "비밀번호는 최소 4자 이상이어야 합니다."
        elif password != password_confirm:
            error_message = "비밀번호 확인이 일치하지 않습니다."
        elif User.objects.filter(username=username).exists():
            error_message = "이미 사용 중인 아이디입니다."
        else:
            new_user = User.objects.create_user(username=username, password=password)
            login(request, new_user)
            return redirect("curation:index")

    return render(request, "curation/signup.html", {"error_message": error_message})


@require_http_methods(["GET", "POST"])
def logout_view(request: HttpRequest) -> HttpResponse:
    """사용자 로그아웃 뷰."""
    logout(request)
    return redirect("curation:login")


@ensure_csrf_cookie
@login_required
@require_GET
def index(request: HttpRequest) -> HttpResponse:
    """메인 대시보드 뷰 (로그인 필수)."""
    from django.conf import settings
    from dotenv import load_dotenv

    load_dotenv(settings.BASE_DIR / ".env", override=True)
    has_naver_id = bool(os.getenv("NAVER_CLIENT_ID", "").strip())
    has_naver_secret = bool(os.getenv("NAVER_CLIENT_SECRET", "").strip())
    has_gemini = bool(os.getenv("GEMINI_API_KEY", "").strip())

    context: dict[str, Any] = {
        "has_naver_keys": has_naver_id and has_naver_secret,
        "has_gemini_key": has_gemini,
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        "all_keys_ready": has_naver_id and has_naver_secret and has_gemini,
    }
    return render(request, "curation/index.html", context)


@csrf_exempt
@require_POST
def curate_api(request: HttpRequest) -> JsonResponse:
    """사용자의 키워드와 필터링 프롬프트를 접수하여 네이버 검색 및 Gemini 큐레이션을 실행하는 API."""
    if not request.user.is_authenticated:
        return JsonResponse(
            {"status": "error", "code": "UNAUTHORIZED", "message": "로그인이 필요한 서비스입니다."},
            status=401,
        )

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


@csrf_exempt
@require_POST
def save_summary_api(request: HttpRequest) -> JsonResponse:
    """AI 요약 결과를 데이터베이스에 저장하는 API (로그인 사용자별 분리)."""
    if not request.user.is_authenticated:
        return JsonResponse(
            {"status": "error", "code": "UNAUTHORIZED", "message": "로그인이 필요한 서비스입니다."},
            status=401,
        )

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
                    user=request.user,
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
        user=request.user,
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
@login_required
@require_GET
def history_view(request: HttpRequest) -> HttpResponse:
    """사용자가 저장한 뉴스 요약 히스토리 페이지 뷰 (본인 데이터만 조회)."""
    summaries = SavedSummary.objects.filter(user=request.user)
    context: dict[str, Any] = {
        "summaries": summaries,
        "total_count": summaries.count(),
    }
    return render(request, "curation/history.html", context)


@csrf_exempt
@require_POST
def delete_summary_api(request: HttpRequest, item_id: int) -> JsonResponse:
    """저장된 뉴스 요약 항목을 삭제하는 API (본인 데이터만 삭제 가능)."""
    if not request.user.is_authenticated:
        return JsonResponse(
            {"status": "error", "code": "UNAUTHORIZED", "message": "로그인이 필요한 서비스입니다."},
            status=401,
        )

    try:
        if request.user.is_staff:
            record = SavedSummary.objects.get(id=item_id)
        else:
            record = SavedSummary.objects.get(id=item_id, user=request.user)
        record.delete()
        return JsonResponse({"status": "success", "message": "항목이 정상적으로 삭제되었습니다."})
    except SavedSummary.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "해당 요약 항목을 찾을 수 없거나 삭제 권한이 없습니다."},
            status=404,
        )


@ensure_csrf_cookie
@require_GET
def admin_dashboard_view(request: HttpRequest) -> HttpResponse:
    """관리자(is_staff=True) 전용 통계 대시보드 뷰."""
    if not request.user.is_authenticated:
        return redirect(f"{reverse('curation:login')}?next={request.path}")

    if not request.user.is_staff:
        return render(request, "curation/403.html", status=403)

    total_users_count = User.objects.count()
    staff_users_count = User.objects.filter(is_staff=True).count()
    total_summaries_count = SavedSummary.objects.count()

    # 오늘 생성된 요약 데이터 수
    today_date = timezone.now().date()
    today_summaries_count = SavedSummary.objects.filter(created_at__date=today_date).count()

    # 가장 최근에 생성된 데이터 20건 (작성자 정보 포함, id 역순 보조 정렬)
    recent_summaries = (
        SavedSummary.objects.select_related("user")
        .order_by("-created_at", "-id")[:20]
    )

    context: dict[str, Any] = {
        "total_users_count": total_users_count,
        "staff_users_count": staff_users_count,
        "total_summaries_count": total_summaries_count,
        "today_summaries_count": today_summaries_count,
        "recent_summaries": recent_summaries,
    }
    return render(request, "curation/admin_dashboard.html", context)
