"""Gemini 뉴스 큐레이션 서비스 단위 테스트."""

import json
from unittest.mock import MagicMock, patch

import pytest

from curation.services.gemini_service import (
    GeminiCurationError,
    curate_and_summarize,
)
from curation.services.models import RawArticle
from curation.services.naver_service import MissingAPIKeyError


def test_curate_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Gemini API 키 미설정 시 MissingAPIKeyError 예외 발생 테스트."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    articles = [RawArticle(index=1, title="기사 1", link="https://a.com", description="요약 1")]

    with pytest.raises(MissingAPIKeyError) as exc_info:
        curate_and_summarize(articles, filter_prompt="테스트")
    assert "Gemini API 키가 설정되지 않았습니다" in str(exc_info.value)


def test_curate_empty_articles(monkeypatch: pytest.MonkeyPatch) -> None:
    """기사 목록이 비어있을 때 에러 발생 테스트."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    with pytest.raises(GeminiCurationError) as exc_info:
        curate_and_summarize([], filter_prompt="테스트")
    assert "분석할 기사 목록이 비어 있습니다" in str(exc_info.value)


@patch("google.genai.Client")
def test_curate_and_summarize_success(
    mock_client_cls: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Gemini AI의 정상 응답 파싱 및 3개 기사 선정 테스트."""
    monkeypatch.setenv("GEMINI_API_KEY", "dummy_key")

    mock_articles = [
        RawArticle(
            index=i,
            title=f"뉴스 기사 {i}",
            link=f"https://news.com/{i}",
            description=f"내용 요약 {i}",
        )
        for i in range(1, 21)
    ]

    mock_response = MagicMock()
    mock_response.text = json.dumps(
        {
            "selected_articles": [
                {
                    "article_index": 2,
                    "title": "뉴스 기사 2",
                    "link": "https://news.com/2",
                    "reason": "필터 기준과 일치함",
                    "summary_bullets": ["요약1", "요약2", "요약3"],
                    "key_insight": "핵심 인사이트 1",
                },
                {
                    "article_index": 5,
                    "title": "뉴스 기사 5",
                    "link": "https://news.com/5",
                    "reason": "기술 혁신 내용 포함",
                    "summary_bullets": ["요약A", "요약B", "요약C"],
                    "key_insight": "핵심 인사이트 2",
                },
                {
                    "article_index": 9,
                    "title": "뉴스 기사 9",
                    "link": "https://news.com/9",
                    "reason": "글로벌 상용화 사례",
                    "summary_bullets": ["소식1", "소식2", "소식3"],
                    "key_insight": "핵심 인사이트 3",
                },
            ]
        }
    )

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    mock_client_cls.return_value = mock_client

    results = curate_and_summarize(mock_articles, filter_prompt="상용화 사례 위주")
    assert len(results) == 3
    assert results[0].article_index == 2
    assert len(results[0].summary_bullets) == 3
    assert results[0].key_insight == "핵심 인사이트 1"
