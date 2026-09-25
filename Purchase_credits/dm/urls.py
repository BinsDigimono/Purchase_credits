from django.urls import path

from . import views

app_name = "dm"

urlpatterns = [
    path("", views.thread_list, name="thread_list"),
    path("start/<int:pk>/", views.start, name="start"),
    path("<int:pk>/", views.thread_detail, name="thread_detail"),
    path("<int:pk>/send/", views.send, name="send"),
    path("<int:pk>/refuse/", views.ai_refuse, name="ai_refuse"),
]
