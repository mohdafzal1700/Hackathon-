from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .serializers import UserSerializer,CustomTokenObtainPairSerializer
from django.db import IntegrityError
from rest_framework_simplejwt.views import TokenObtainPairView


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