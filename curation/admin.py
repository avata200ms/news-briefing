"""curation 앱의 Django 관리자 페이지 설정."""

from django.contrib import admin

from curation.models import SavedSummary


@admin.register(SavedSummary)
class SavedSummaryAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "keyword", "created_at")
    list_filter = ("created_at", "keyword")
    search_fields = ("title", "summary", "reason", "keyword")
    readonly_fields = ("created_at",)
