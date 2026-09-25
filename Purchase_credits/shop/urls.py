from django.urls import path

from . import views

app_name = "shop"

urlpatterns = [
    path("subjects/", views.subject_list, name="subject_list"),
    path("subjects/<int:pk>/", views.subject_detail, name="subject_detail"),
    path("cart/", views.cart, name="cart"),
    path("cart/add/<int:pk>/", views.cart_add, name="cart_add"),
    path("cart/remove/<int:pk>/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.order_list, name="order_list"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
]
