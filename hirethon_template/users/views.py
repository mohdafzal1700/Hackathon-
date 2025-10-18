from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .serializers import UserSerializer,CustomTokenObtainPairSerializer
from django.db import IntegrityError
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from google.oauth2 import id_token
from google.auth.transport import requests

class SignupView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.save()  

            return Response({
                "message": "User created successfully. Please login to get access token.",
                "user": UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)

        except IntegrityError:
            return Response({
                "error": "A user with this username or email already exists."
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "error": "Signup failed.",
                "details": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()  # blacklist the token

            return Response({"message": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)

        except KeyError:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        except TokenError:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        id_token_str = request.data.get("id_token")
        if not id_token_str:
            return Response({"error": "Missing id_token"}, status=400)

        try:
            idinfo = id_token.verify_oauth2_token(
                id_token_str,
                requests.Request(),
                settings.GOOGLE_OAUTH2_CLIENT_ID
            )
        except ValueError:
            return Response({"error": "Invalid token"}, status=400)

        email = idinfo.get("email")
        name = idinfo.get("name", "")
        username = email

        user, created = User.objects.get_or_create(
            email=email,
            defaults={"username": username, "first_name": name, "is_active": True}
        )

        # If newly created, create default org and membership
        if created:
            org = Organization.objects.create(name=f"{user.username}'s Org")
            Membership.objects.create(user=user, organization=org, role="Admin")

        # Generate JWT
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response({
            "message": "Google authentication successful",
            "user": {"id": user.id, "email": user.email, "username": user.username},
            "access": str(access),
            "refresh": str(refresh),
            "is_new_user": created,
        }, status=200)

