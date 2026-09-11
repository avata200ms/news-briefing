"""Google Gemini API를 활용한 뉴스 큐레이션 및 요약 서비스."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from curation.services.models import CuratedArticle, GeminiCurationOutput, RawArticle
from curation.services.naver_service import MissingAPIKeyError

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env", override=True)


class GeminiCurationError(Exception):
    """Gemini 큐레이션 분석 중 발생하는 예외."""

    pass


def curate_and_summarize(articles: list[RawArticle], filter_prompt: str) -> list[CuratedArticle]:
    """수집된 20개 기사 중 필터링 프롬프트 기준에 가장 적합한 3개 기사를 선정 및 요약합니다.

    Args:
        articles: 네이버에서 수집한 20개 기사 리스트
        filter_prompt: 사용자가 지정한 기사 선별 기준 프롬프트

    Returns:
        선정된 3개 기사의 상세 큐레이션 결과 리스트 (CuratedArticle)

    Raises:
        MissingAPIKeyError: GEMINI_API_KEY가 없을 때
        GeminiCurationError: 모델 호출 또는 결과 파싱 실패 시
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise MissingAPIKeyError(
            "Gemini API 키가 설정되지 않았습니다. .env 파일에 GEMINI_API_KEY를 입력해주세요. (https://aistudio.google.com/)"
        )

    if not articles:
        raise GeminiCurationError("분석할 기사 목록이 비어 있습니다.")

    model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()
    # 구글에서 404를 반환하는 구버전 모델(2.5 등) 또는 빈 값일 경우 자동으로 gemini-3.6-flash로 대체
    if not model_name or "2.5" in model_name or "1.5" in model_name:
        model_name = "gemini-3.6-flash"

    # 기사 목록 텍스트 구성
    articles_text_blocks: list[str] = []
    for art in articles:
        articles_text_blocks.append(
            f"[{art.index}번 기사]\n제목: {art.title}\n요약: {art.description}\n링크: {art.link}\n"
        )
    articles_text = "\n".join(articles_text_blocks)

    system_instruction = (
        "당신은 최고 수준의 전문 IT/비즈니스 뉴스 큐레이터이자 데이터 분석가입니다.\n"
        "제공되는 20개의 뉴스 기사 목록을 정밀 분석하고, 사용자가 제시한 '필터링 기준 프롬프트'에 가장 정확하게 부합하는 기사 "
        "정확히 3개를 선별해야 합니다.\n\n"
        "선별된 3개의 기사에 대해 반드시 다음 요구사항을 충족하십시오:\n"
        "1. reason: 사용자의 필터링 기준과 어떻게 부합하여 이 기사를 선별했는지 구체적 근거를 명시할 것.\n"
        "2. summary_bullets: 기사의 핵심 내용을 3개의 완전한 문장으로 요약할 것.\n"
        "3. key_insight: 이 기사가 주는 시사점이나 독자가 주목해야 할 핵심 가치를 1문장의 인사이트로 정리할 것.\n"
        "4. 원본 기사의 article_index(1~20), title, link를 정확히 매핑할 것."
    )

    prompt = (
        f"### [사용자의 기사 필터링 기준]\n"
        f'"{filter_prompt}"\n\n'
        f"### [검색된 뉴스 기사 20건 목록]\n"
        f"{articles_text}\n\n"
        f"위 20건의 기사 중에서 사용자의 필터링 기준에 가장 잘 맞는 기사 **정확히 3건**을 선정하여 응답 스키마에 맞게 JSON으로 출력해 주세요."
    )

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
                response_mime_type="application/json",
                response_schema=GeminiCurationOutput,
            ),
        )

        raw_json = response.text
        if not raw_json:
            raise GeminiCurationError("Gemini 모델로부터 응답을 받지 못했습니다.")

        data = json.loads(raw_json)
        curated_output = GeminiCurationOutput.model_validate(data)

        # 원본 기사와 링크/제목 무결성 보정
        articles_by_index = {a.index: a for a in articles}
        final_selected: list[CuratedArticle] = []

        for item in curated_output.selected_articles:
            orig = articles_by_index.get(item.article_index)
            if orig:
                # 원본의 정제된 링크와 제목 보장
                curated_item = CuratedArticle(
                    article_index=orig.index,
                    title=orig.title if not item.title else item.title,
                    link=orig.link,
                    reason=item.reason,
                    summary_bullets=item.summary_bullets,
                    key_insight=item.key_insight,
                )
            else:
                curated_item = item
            final_selected.append(curated_item)

        # 혹시 3개보다 많거나 적을 경우 최대 3개로 제한
        return final_selected[:3]

    except Exception as exc:
        if isinstance(exc, MissingAPIKeyError):
            raise
        raise GeminiCurationError(f"Gemini 뉴스 큐레이션 실패: {exc}") from exc
