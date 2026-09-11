"""뉴스 큐레이션 도메인 모델 정의."""

from typing import Any

from pydantic import BaseModel, Field


class RawArticle(BaseModel):
    """네이버 검색 API에서 수집된 원본 기사 모델."""

    index: int = Field(description="1부터 시작하는 기사 번호")
    title: str = Field(description="정제된 기사 제목")
    link: str = Field(description="기사 링크 (네이버 뉴스 또는 언론사 링크)")
    originallink: str = Field(default="", description="언론사 원문 링크")
    description: str = Field(description="정제된 기사 본문 요약")
    pub_date: str = Field(default="", description="기사 발행일시")


class CuratedArticle(BaseModel):
    """Gemini AI가 필터링 기준으로 선정한 기사 모델."""

    article_index: int = Field(description="선정된 기사의 원본 번호 (1~20)")
    title: str = Field(description="기사 제목")
    link: str = Field(description="기사 링크")
    reason: str = Field(description="필터링 기준에 부합하여 선정한 구체적 이유")
    summary_bullets: list[str] = Field(description="기사 핵심 내용 3줄 요약 (리스트)")
    key_insight: str = Field(description="기사의 핵심 시사점 및 한 줄 인사이트")


class GeminiCurationOutput(BaseModel):
    """Gemini 모델로부터 전달받는 구조화된 응답 스키마."""

    selected_articles: list[CuratedArticle] = Field(
        description="사용자 기준에 맞게 선정된 정확히 3개의 기사 목록"
    )


class CurationResult(BaseModel):
    """최종 큐레이션 결과 응답 모델."""

    keyword: str
    filter_prompt: str
    total_searched: int
    curated_articles: list[CuratedArticle]
    raw_articles: list[RawArticle]
    metadata: dict[str, Any] = Field(default_factory=dict)
