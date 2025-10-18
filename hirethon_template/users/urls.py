from django.urls import path
from .views import SignupView, LoginView, LogoutView
app_name = "users" 
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("register/", SignupView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
