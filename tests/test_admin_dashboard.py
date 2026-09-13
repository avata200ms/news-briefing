"""커스텀 관리자 대시보드 권한 및 기능 테스트."""

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from curation.models import SavedSummary


@pytest.fixture
def normal_user(db):
    """일반 회원 픽스처."""
    return User.objects.create_user(username="regular_user", password="password123")


@pytest.fixture
def staff_user(db):
    """스태프 관리자 픽스처."""
    return User.objects.create_user(
        username="staff_admin",
        password="password123",
        is_staff=True,
    )


@pytest.mark.django_db
def test_admin_dashboard_anonymous_redirect(client: Client):
    """비로그인 유저는 로그인 페이지로 리다이렉트되어야 함."""
    url = reverse("curation:admin_dashboard")
    response = client.get(url)
    assert response.status_code == 302
    assert "/login/" in response.url
    assert "next=" in response.url


@pytest.mark.django_db
def test_admin_dashboard_normal_user_forbidden(client: Client, normal_user: User):
    """일반 유저(is_staff=False)는 403 Forbidden 응답을 받아야 함."""
    client.force_login(normal_user)
    url = reverse("curation:admin_dashboard")
    response = client.get(url)
    assert response.status_code == 403
    assert "관리자 전용 페이지입니다" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_admin_dashboard_staff_access_success(client: Client, staff_user: User, normal_user: User):
    """스태프 관리자(is_staff=True)는 200 OK와 함께 통계 및 최근 20건 데이터를 확인해야 함."""
    # 더미 요약 데이터 생성
    for i in range(25):
        SavedSummary.objects.create(
            user=normal_user if i % 2 == 0 else staff_user,
            title=f"테스트 뉴스 제목 {i}",
            summary=f"테스트 뉴스 요약 내용 {i}",
            link=f"https://news.example.com/{i}",
        )

    client.force_login(staff_user)
    url = reverse("curation:admin_dashboard")
    response = client.get(url)

    assert response.status_code == 200
    content = response.content.decode("utf-8")

    # 통계 지표 검증
    assert "통계 모니터링 패널" in content
    assert "Total Users" in content
    assert "Total Saved Summaries" in content
    assert "25" in content  # 전체 요약 25건

    # 최근 20건 표시 검증 (25번째부터 5번째까지 20개 표시, 0~4번은 미표시)
    assert "테스트 뉴스 제목 24" in content
    assert "테스트 뉴스 제목 5" in content


@pytest.mark.django_db
def test_header_admin_button_visibility(client: Client, staff_user: User, normal_user: User):
    """스태프 로그인 시 관리자 패널 버튼이 보이고, 일반 유저 로그인 시 보이지 않아야 함."""
    index_url = reverse("curation:index")

    # 1. 일반 유저로 로그인
    client.force_login(normal_user)
    res_normal = client.get(index_url)
    assert res_normal.status_code == 200
    assert "btn-nav-admin" not in res_normal.content.decode("utf-8")

    # 2. 스태프 관리자로 로그인
    client.force_login(staff_user)
    res_staff = client.get(index_url)
    assert res_staff.status_code == 200
    assert "btn-nav-admin" in res_staff.content.decode("utf-8")
    assert "관리자 패널" in res_staff.content.decode("utf-8")


@pytest.mark.django_db
def test_staff_delete_other_user_summary(client: Client, staff_user: User, normal_user: User):
    """스태프 관리자는 다른 사용자의 요약도 삭제 관리할 수 있어야 함."""
    record = SavedSummary.objects.create(
        user=normal_user,
        title="일반 사용자의 뉴스",
        summary="일반 사용자의 요약 내용",
        link="https://example.com/item",
    )

    client.force_login(staff_user)
    del_url = reverse("curation:delete_summary_api", kwargs={"item_id": record.id})
    res = client.post(del_url)
    assert res.status_code == 200
    assert res.json().get("status") == "success"
    assert not SavedSummary.objects.filter(id=record.id).exists()
