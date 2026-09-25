from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # トップページがログイン画面を兼ねている（メンテナンス告知に見せかけたもの）
    path(
        "",
        auth_views.LoginView.as_view(
            template_name="portal.html", redirect_authenticated_user=True
        ),
        name="portal",
    ),
    path("robots.txt", views.robots_txt, name="robots"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
