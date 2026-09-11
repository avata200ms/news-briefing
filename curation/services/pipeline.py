"""네이버 뉴스 검색 및 Gemini 큐레이션 통합 파이프라인."""

import logging

from curation.services.gemini_service import curate_and_summarize
from curation.services.models import CuratedArticle, CurationResult, RawArticle
from curation.services.naver_service import fetch_naver_news

logger = logging.getLogger(__name__)


def generate_mock_data(keyword: str, filter_prompt: str) -> CurationResult:
    """API 키가 설정되지 않은 환경에서 UI 및 인터랙션을 테스트하기 위한 데모 데이터 생성."""
    mock_raw = [
        RawArticle(
            index=i,
            title=f"[{keyword}] 혁신 기술과 산업 동향 분석 리포트 #{i}",
            link=f"https://news.example.com/article/{i}",
            originallink=f"https://press.example.com/{i}",
            description=f"{keyword} 분야의 최근 시장 변화와 기술 혁신을 다룬 심층 기사입니다. 기업들의 투자와 상용화 사례가 포함되어 있습니다.",
            pub_date="2026-09-11 20:00:00",
        )
        for i in range(1, 21)
    ]

    mock_curated = [
        CuratedArticle(
            article_index=1,
            title=f"[{keyword}] 글로벌 테크 리더들의 상용화 로드맵 발표",
            link="https://news.example.com/article/1",
            reason=f"사용자 필터 기준 '{filter_prompt}'에 가장 완벽하게 부합하며, 구체적인 투자 금액과 일정 정보가 포함되어 선정함.",
            summary_bullets=[
                f"{keyword} 기술의 2026년 하반기 상용화 일정이 공식 확정되었습니다.",
                "주요 선도 기업들이 공동으로 대규모 펀드를 조성하고 생태계 확장에 나섰습니다.",
                "전문가들은 이번 협력이 산업 전반의 패러다임 전환을 이끌 것으로 전망했습니다.",
            ],
            key_insight=f"선도 기업들의 전략적 제휴로 {keyword} 시장 성장이 예상보다 2배 이상 가속화될 전망.",
        ),
        CuratedArticle(
            article_index=3,
            title=f"[{keyword}] 차세대 아키텍처 도입으로 전력 효율 40% 개선 달성",
            link="https://news.example.com/article/3",
            reason="필터링 기준인 실질적인 성능 향상과 양산 적용 가능성을 명확한 정량 지표로 입증함.",
            summary_bullets=[
                "신규 공정 적용을 통해 전력 소비량을 기존 대비 40% 절감하는 데 성공했습니다.",
                "주요 고객사들의 초기 벤치마크 테스트 결과 합격점을 받았습니다.",
                "올해 4분기부터 본격적인 대량 양산에 돌입할 예정입니다.",
            ],
            key_insight="하드웨어 효율성 개선을 통해 데이터센터 운영 비용의 획기적 절감이 기대됨.",
        ),
        CuratedArticle(
            article_index=7,
            title=f"[{keyword}] 글로벌 표준화 기구, 신규 보안 가이드라인 최종 채택",
            link="https://news.example.com/article/7",
            reason="규제 대응 및 신뢰성 확보라는 필터 기준 관점에서 가장 권위 있는 정책 정보를 제공함.",
            summary_bullets=[
                "국제 표준화 기구에서 신규 안전 및 개인정보 보호 가이드라인을 최종 확정했습니다.",
                "국내외 주요 기업들은 이에 맞춘 준수 프로세스를 조기 도입하기로 합의했습니다.",
                "향후 글로벌 시장 진출을 위한 필수 인증 요건으로 자리잡을 예정입니다.",
            ],
            key_insight="표준 규제 선점을 통해 글로벌 시장 진입 장벽을 낮추고 생태계 신뢰성을 확보함.",
        ),
    ]

    return CurationResult(
        keyword=keyword,
        filter_prompt=filter_prompt,
        total_searched=20,
        curated_articles=mock_curated,
        raw_articles=mock_raw,
        metadata={
            "is_demo": True,
            "note": "API 키 미설정으로 인해 데모 프리뷰 모드로 실행되었습니다.",
        },
    )


def run_curation_pipeline(
    keyword: str, filter_prompt: str, allow_demo_fallback: bool = False
) -> CurationResult:
    """네이버 검색과 Gemini 선별 과정을 일괄 실행합니다.

    Args:
        keyword: 검색 키워드
        filter_prompt: 필터링 프롬프트
        allow_demo_fallback: API 키 미설정 시 데모 데이터로 fallback할지 여부

    Returns:
        CurationResult 결과 객체
    """
    keyword = keyword.strip()
    filter_prompt = filter_prompt.strip()

    if not keyword:
        raise ValueError("검색 키워드를 입력해주세요.")
    if not filter_prompt:
        raise ValueError("필터링 프롬프트를 입력해주세요.")

    try:
        # 1단계: 네이버 뉴스 20건 수집
        raw_articles = fetch_naver_news(query=keyword, display=20)

        # 2단계: Gemini AI 3건 선별 및 요약
        curated_articles = curate_and_summarize(articles=raw_articles, filter_prompt=filter_prompt)

        return CurationResult(
            keyword=keyword,
            filter_prompt=filter_prompt,
            total_searched=len(raw_articles),
            curated_articles=curated_articles,
            raw_articles=raw_articles,
            metadata={"is_demo": False},
        )
    except Exception as exc:
        if allow_demo_fallback:
            logger.warning("외부 API 호출 실패 또는 키 오류로 데모 모드로 전환합니다: %s", exc)
            demo_result = generate_mock_data(keyword=keyword, filter_prompt=filter_prompt)
            demo_result.metadata["original_error"] = str(exc)
            return demo_result
        raise
