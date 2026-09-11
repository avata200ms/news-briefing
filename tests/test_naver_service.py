"""네이버 뉴스 검색 서비스 단위 테스트."""

from unittest.mock import MagicMock, patch

import pytest

from curation.services.naver_service import (
    MissingAPIKeyError,
    clean_html,
    fetch_naver_news,
)


def test_clean_html() -> None:
    """HTML 태그 및 특수 엔티티 정제 테스트."""
    raw = "<b>인공지능</b> &amp; <i>로봇</i> &quot;혁신&quot; &lt;미래&gt;"
    cleaned = clean_html(raw)
    assert cleaned == '인공지능 & 로봇 "혁신" <미래>'
    assert "<b>" not in cleaned
    assert "</b>" not in cleaned


def test_fetch_naver_news_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """API 키 미설정 시 MissingAPIKeyError 예외 발생 테스트."""
    monkeypatch.delenv("NAVER_CLIENT_ID", raising=False)
    monkeypatch.delenv("NAVER_CLIENT_SECRET", raising=False)

    with pytest.raises(MissingAPIKeyError) as exc_info:
        fetch_naver_news(query="테스트")
    assert "네이버 검색 API 키가 설정되지 않았습니다" in str(exc_info.value)


@patch("httpx.Client")
def test_fetch_naver_news_success(
    mock_client_cls: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """네이버 API 정상 응답 파싱 테스트."""
    monkeypatch.setenv("NAVER_CLIENT_ID", "dummy_id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "dummy_secret")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {
                "title": "<b>AI</b> 반도체 혁신",
                "link": "https://naver.me/1",
                "originallink": "https://news.com/1",
                "description": "국내 기업의 <b>신기술</b> 개발",
                "pubDate": "Fri, 11 Sep 2026 10:00:00 +0900",
            }
            for i in range(20)
        ]
    }

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = mock_response
    mock_client_cls.return_value = mock_client

    articles = fetch_naver_news(query="AI 반도체", display=20)
    assert len(articles) == 20
    assert articles[0].index == 1
    assert articles[0].title == "AI 반도체 혁신"
    assert articles[0].description == "국내 기업의 신기술 개발"
