"""Django 웹 뷰 및 API 통합 테스트."""

import json

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_index_view_status() -> None:
    """메인 대시보드 페이지 GET 요청 성공 테스트 (로그인 상태)."""
    user = User.objects.create_user(username="view_tester", password="pw")
    client = Client()
    client.force_login(user)

    response = client.get(reverse("curation:index"))
    assert response.status_code == 200
    assert "AI 뉴스 큐레이터" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_curate_api_missing_fields() -> None:
    """필수 필드(keyword, filter_prompt) 누락 시 400 에러 테스트."""
    user = User.objects.create_user(username="curate_tester", password="pw")
    client = Client()
    client.force_login(user)

    # 키워드 누락
    response = client.post(
        reverse("curation:curate_api"),
        data=json.dumps({"keyword": "", "filter_prompt": "조건"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "검색 키워드를 입력해 주세요" in response.json()["message"]

    # 프롬프트 누락
    response = client.post(
        reverse("curation:curate_api"),
        data=json.dumps({"keyword": "AI", "filter_prompt": ""}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "필터링 프롬프트를 입력해 주세요" in response.json()["message"]


@pytest.mark.django_db
def test_curate_api_demo_fallback(monkeypatch) -> None:
    """API 키 미설정 시 데모 데이터 fallback 200 반환 테스트."""
    monkeypatch.delenv("NAVER_CLIENT_ID", raising=False)
    monkeypatch.delenv("NAVER_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    user = User.objects.create_user(username="demo_tester", password="pw")
    client = Client()
    client.force_login(user)

    response = client.post(
        reverse("curation:curate_api"),
        data=json.dumps(
            {
                "keyword": "양자 컴퓨팅",
                "filter_prompt": "투자 및 성과 위주",
                "allow_demo": True,
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert len(res_data["data"]["curated_articles"]) == 3
    assert res_data["data"]["total_searched"] == 20
    assert res_data["data"]["metadata"]["is_demo"] is True
