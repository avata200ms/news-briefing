"""네이버 뉴스 검색 API 연동 서비스."""

import html
import os
import re
from typing import Any

import httpx
from dotenv import load_dotenv

from curation.services.models import RawArticle

load_dotenv()


class NaverAPIError(Exception):
    """네이버 API 호출 관련 예외."""

    pass


class MissingAPIKeyError(Exception):
    """필수 API 키가 설정되지 않았을 때 발생하는 예외."""

    pass


def clean_html(raw_html: str) -> str:
    """HTML 태그 제거 및 특수 문자 엔티티를 디코딩합니다."""
    if not raw_html:
        return ""
    # <b>, </b> 등 모든 HTML 태그 제거
    clean_text = re.sub(r"<[^>]+>", "", raw_html)
    # &quot;, &amp;, &lt;, &gt; 등 엔티티 디코딩
    clean_text = html.unescape(clean_text)
    # 연속된 공백 정리
    clean_text = re.sub(r"\s+", " ", clean_text).strip()
    return clean_text


def fetch_naver_news(query: str, display: int = 20) -> list[RawArticle]:
    """네이버 검색 API를 통해 최신 뉴스 기사를 수집합니다.

    Args:
        query: 검색 키워드
        display: 수집할 기사 수 (기본값 20)

    Returns:
        정제된 RawArticle 리스트

    Raises:
        MissingAPIKeyError: 네이버 Client ID / Secret이 없을 때
        NaverAPIError: API 호출 실패 시
    """
    client_id = os.getenv("NAVER_CLIENT_ID", "").strip()
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        raise MissingAPIKeyError(
            "네이버 검색 API 키가 설정되지 않았습니다. .env 파일에 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 입력해주세요. (https://developers.naver.com/apps/#/register)"
        )

    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "User-Agent": "NewsBriefingApp/1.0",
    }
    params: dict[str, Any] = {
        "query": query,
        "display": display,
        "sort": "sim",  # 정확도순
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, headers=headers, params=params)

        if response.status_code != 200:
            error_data = (
                response.json()
                if response.headers.get("content-type", "").startswith("application/json")
                else {}
            )
            error_msg = error_data.get("errorMessage", response.text)
            raise NaverAPIError(
                f"네이버 뉴스 검색 실패 (상태 코드: {response.status_code}): {error_msg}"
            )

        data = response.json()
        items = data.get("items", [])

        articles: list[RawArticle] = []
        for idx, item in enumerate(items, start=1):
            articles.append(
                RawArticle(
                    index=idx,
                    title=clean_html(item.get("title", "")),
                    link=item.get("link", "") or item.get("originallink", ""),
                    originallink=item.get("originallink", ""),
                    description=clean_html(item.get("description", "")),
                    pub_date=item.get("pubDate", ""),
                )
            )

        return articles

    except httpx.RequestError as exc:
        raise NaverAPIError(f"네이버 API 네트워크 통신 오류: {exc}") from exc
