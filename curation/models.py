"""뉴스 큐레이션 데이터베이스 모델 정의."""

from django.contrib.auth.models import User
from django.db import models


class SavedSummary(models.Model):
    """사용자가 저장한 뉴스 요약 결과 모델."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="saved_summaries",
        null=True,
        blank=True,
        verbose_name="저장한 사용자",
    )
    title = models.CharField(max_length=500, verbose_name="뉴스 제목")
    summary = models.TextField(verbose_name="요약 본문")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="저장 시간")

    # 부가 정보 (원문 링크, AI 선정 이유, 인사이트, 검색 키워드)
    link = models.URLField(max_length=1000, blank=True, default="", verbose_name="기사 원문 링크")
    reason = models.TextField(blank=True, default="", verbose_name="AI 선정 이유")
    insight = models.TextField(blank=True, default="", verbose_name="핵심 인사이트")
    keyword = models.CharField(max_length=200, blank=True, default="", verbose_name="검색 키워드")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "저장된 뉴스 요약"
        verbose_name_plural = "저장된 뉴스 요약 목록"

    def __str__(self) -> str:
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {self.title[:40]}"

    def summary_lines(self) -> list[str]:
        """줄바꿈으로 구분된 요약 본문을 리스트로 반환합니다."""
        return [line.strip() for line in self.summary.split("\n") if line.strip()]
