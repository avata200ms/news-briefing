"""Django 웹 뷰 및 API 통합 테스트."""

import json

from django.test import Client
from django.urls import reverse


def test_index_view_status() -> None:
    """메인 대시보드 페이지 GET 요청 성공 테스트."""
    client = Client()
    response = client.get(reverse("curation:index"))
    assert response.status_code == 200
    assert "AI 뉴스 큐레이터" in response.content.decode("utf-8")


def test_curate_api_missing_fields() -> None:
    """필수 필드(keyword, filter_prompt) 누락 시 400 에러 테스트."""
    client = Client()
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


def test_curate_api_demo_fallback() -> None:
    """API 키 미설정 시 데모 데이터 fallback 200 반환 테스트."""
    client = Client()
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
