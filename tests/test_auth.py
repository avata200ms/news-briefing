"""사용자 인증(회원가입, 로그인, 로그아웃) 및 권한/데이터 격리 단위 테스트."""

import json

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from curation.models import SavedSummary


def test_anonymous_user_redirect_to_login() -> None:
    """비로그인 사용자가 메인 페이지와 히스토리 페이지 접근 시 로그인 페이지로 리다이렉트되는지 검증."""
    client = Client()

    # 메인 페이지 접근 시
    res_index = client.get(reverse("curation:index"))
    assert res_index.status_code == 302
    assert reverse("curation:login") in res_index.url

    # 히스토리 페이지 접근 시
    res_history = client.get(reverse("curation:history"))
    assert res_history.status_code == 302
    assert reverse("curation:login") in res_history.url


def test_anonymous_user_api_access_blocked() -> None:
    """비로그인 사용자가 API 호출 시 401 Unauthorized 반환 검증."""
    client = Client()

    # 큐레이션 API
    res_curate = client.post(
        reverse("curation:curate_api"),
        data=json.dumps({"keyword": "AI", "filter_prompt": "조건"}),
        content_type="application/json",
    )
    assert res_curate.status_code == 401
    assert res_curate.json()["code"] == "UNAUTHORIZED"

    # 요약 저장 API
    res_save = client.post(
        reverse("curation:save_summary_api"),
        data=json.dumps({"title": "제목", "summary": "요약"}),
        content_type="application/json",
    )
    assert res_save.status_code == 401
    assert res_save.json()["code"] == "UNAUTHORIZED"


@pytest.mark.django_db
def test_user_signup_and_duplicate_check() -> None:
    """회원가입 성공 및 동일 아이디 중복 생성 방지 검증."""
    client = Client()

    # 정상 회원가입
    res_signup = client.post(
        reverse("curation:signup"),
        data={
            "username": "tester1",
            "password": "password1234",
            "password_confirm": "password1234",
        },
    )
    assert res_signup.status_code == 302
    assert res_signup.url == reverse("curation:index")
    assert User.objects.filter(username="tester1").exists()

    # 중복 아이디 가입 시도
    client.logout()
    res_dup = client.post(
        reverse("curation:signup"),
        data={
            "username": "tester1",
            "password": "password1234",
            "password_confirm": "password1234",
        },
    )
    assert res_dup.status_code == 200
    assert "이미 사용 중인 아이디입니다" in res_dup.content.decode("utf-8")


@pytest.mark.django_db
def test_user_login_and_logout() -> None:
    """사용자 로그인 성공, 실패 및 로그아웃 동작 검증."""
    User.objects.create_user(username="validuser", password="secretpassword")
    client = Client()

    # 잘못된 비밀번호로 로그인
    res_fail = client.post(
        reverse("curation:login"),
        data={"username": "validuser", "password": "wrongpassword"},
    )
    assert res_fail.status_code == 200
    assert "아이디 또는 비밀번호가 올바르지 않습니다" in res_fail.content.decode("utf-8")

    # 정상 로그인
    res_success = client.post(
        reverse("curation:login"),
        data={"username": "validuser", "password": "secretpassword"},
    )
    assert res_success.status_code == 302
    assert res_success.url == "/"

    # 로그인 상태에서 메인 대시보드 접근 확인
    res_main = client.get(reverse("curation:index"))
    assert res_main.status_code == 200
    assert "validuser" in res_main.content.decode("utf-8")

    # 로그아웃
    res_logout = client.get(reverse("curation:logout"))
    assert res_logout.status_code == 302
    assert res_logout.url == reverse("curation:login")

    # 로그아웃 후 메인 접근 시 다시 리다이렉트 확인
    res_after = client.get(reverse("curation:index"))
    assert res_after.status_code == 302


@pytest.mark.django_db
def test_user_data_isolation() -> None:
    """사용자 A와 사용자 B 간의 저장된 요약 데이터 격리 검증."""
    user_a = User.objects.create_user(username="userA", password="passwordA")
    user_b = User.objects.create_user(username="userB", password="passwordB")

    client_a = Client()
    client_a.force_login(user_a)

    # 사용자 A가 요약 1건 저장
    res_save = client_a.post(
        reverse("curation:save_summary_api"),
        data=json.dumps(
            {
                "title": "A의 비공개 AI 뉴스",
                "summary": "A만의 특별한 요약 본문입니다.",
                "keyword": "인공지능",
            }
        ),
        content_type="application/json",
    )
    assert res_save.status_code == 200
    item_id = res_save.json()["saved_id"]

    # 사용자 A의 히스토리 페이지에는 해당 기사가 나타남
    res_history_a = client_a.get(reverse("curation:history"))
    assert "A의 비공개 AI 뉴스" in res_history_a.content.decode("utf-8")

    # 사용자 B로 로그인 후 히스토리 확인 -> A의 데이터가 노출되지 않음
    client_b = Client()
    client_b.force_login(user_b)
    res_history_b = client_b.get(reverse("curation:history"))
    assert "A의 비공개 AI 뉴스" not in res_history_b.content.decode("utf-8")
    assert res_history_b.context["total_count"] == 0

    # 사용자 B가 사용자 A의 데이터 삭제 시도 시 차단 확인 (404 권한 없음)
    res_delete = client_b.post(reverse("curation:delete_summary_api", args=[item_id]))
    assert res_delete.status_code == 404
    assert SavedSummary.objects.filter(id=item_id).exists()

    # 사용자 A 본인이 삭제 시 성공 확인
    res_delete_a = client_a.post(reverse("curation:delete_summary_api", args=[item_id]))
    assert res_delete_a.status_code == 200
    assert not SavedSummary.objects.filter(id=item_id).exists()
