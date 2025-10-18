from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from django.conf import settings
from .models import User,Organization,Membership,Invite,Namespace,ShortURL
import re
import logging 
import uuid


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email", "password"]  # ✅ Changed username to name
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        org = Organization.objects.create(
            name=f"{user.name}'s Org",  # ✅ Changed username to name
            created_by=user
        )
        Membership.objects.create(user=user, organization=org, role="Admin")
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    # Override to accept email instead of username
    username_field = 'email'
    
    def validate(self, attrs):
        data = super().validate(attrs)
        # Include user info with correct field name
        data.update({
            "user": {
                "id": self.user.id,
                "name": self.user.name, 
                "email": self.user.email,
            }
        })
        return data
    
    