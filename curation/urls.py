"""curation 앱 URL 라우팅 설정."""

from django.urls import path

from curation import views

app_name = "curation"

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    path("history/", views.history_view, name="history"),
    path("api/curate/", views.curate_api, name="curate_api"),
    path("api/save/", views.save_summary_api, name="save_summary_api"),
    path("api/history/<int:item_id>/delete/", views.delete_summary_api, name="delete_summary_api"),
]
