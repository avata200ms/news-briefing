"""curation 앱 URL 라우팅 설정."""

from django.urls import path

from curation import views

app_name = "curation"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/curate/", views.curate_api, name="curate_api"),
]
