"""뉴스 요약 저장 및 히스토리 기능 테스트."""

import json

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from curation.models import SavedSummary


@pytest.mark.django_db
def test_saved_summary_model() -> None:
    """SavedSummary 모델 필드 및 메서드 동작 테스트."""
    item = SavedSummary.objects.create(
        title="테스트 AI 기사",
        summary="요약 첫 번째 줄\n요약 두 번째 줄\n요약 세 번째 줄",
        link="https://example.com/test",
        reason="테스트 선정 이유",
        insight="테스트 인사이트",
        keyword="AI",
    )
    assert item.id is not None
    assert str(item).endswith("테스트 AI 기사")
    lines = item.summary_lines()
    assert len(lines) == 3
    assert lines[0] == "요약 첫 번째 줄"


@pytest.mark.django_db
def test_save_summary_api_single() -> None:
    """단건 요약 저장 API 테스트."""
    user = User.objects.create_user(username="single_saver", password="pw")
    client = Client()
    client.force_login(user)

    payload = {
        "title": "단건 저장 기사 제목",
        "summary_bullets": ["요약1", "요약2", "요약3"],
        "link": "https://example.com/single",
        "reason": "필터 부합",
        "key_insight": "향후 전망 밝음",
        "keyword": "반도체",
    }
    response = client.post(
        reverse("curation:save_summary_api"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "saved_id" in data

    saved = SavedSummary.objects.get(id=data["saved_id"])
    assert saved.title == "단건 저장 기사 제목"
    assert "요약1\n요약2\n요약3" in saved.summary
    assert saved.keyword == "반도체"
    assert saved.user == user


@pytest.mark.django_db
def test_save_summary_api_batch() -> None:
    """다건(일괄) 요약 저장 API 테스트."""
    user = User.objects.create_user(username="batch_saver", password="pw")
    client = Client()
    client.force_login(user)

    payload = {
        "items": [
            {"title": "기사 1", "summary_bullets": ["요약 1"], "link": "https://1.com"},
            {"title": "기사 2", "summary_bullets": ["요약 2"], "link": "https://2.com"},
            {"title": "기사 3", "summary_bullets": ["요약 3"], "link": "https://3.com"},
        ],
        "keyword": "양자 컴퓨팅",
    }
    response = client.post(
        reverse("curation:save_summary_api"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["saved_ids"]) == 3
    assert SavedSummary.objects.filter(keyword="양자 컴퓨팅", user=user).count() == 3


@pytest.mark.django_db
def test_history_view() -> None:
    """나의 요약 히스토리 페이지 조회 테스트."""
    user = User.objects.create_user(username="history_tester", password="pw")
    SavedSummary.objects.create(
        user=user,
        title="히스토리 확인 기사",
        summary="내용 요약",
        keyword="로봇",
    )
    client = Client()
    client.force_login(user)

    response = client.get(reverse("curation:history"))
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "나의 요약 히스토리" in content
    assert "히스토리 확인 기사" in content
    assert "로봇" in content


@pytest.mark.django_db
def test_delete_summary_api() -> None:
    """저장된 요약 삭제 API 테스트."""
    user = User.objects.create_user(username="delete_tester", password="pw")
    item = SavedSummary.objects.create(
        user=user,
        title="삭제 대상 기사",
        summary="삭제될 내용",
    )
    client = Client()
    client.force_login(user)

    # 정상 삭제
    response = client.post(reverse("curation:delete_summary_api", kwargs={"item_id": item.id}))
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert not SavedSummary.objects.filter(id=item.id).exists()

    # 존재하지 않는 ID 삭제 시 404
    response_404 = client.post(reverse("curation:delete_summary_api", kwargs={"item_id": 99999}))
    assert response_404.status_code == 404
