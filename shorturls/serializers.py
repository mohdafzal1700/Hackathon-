from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from .models import User,Organization,Membership,Invite,Namespace,ShortURL
import re
import logging 
import uuid

class NamespaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Namespace
        fields = ["id", "organization", "name", "created_by", "created_at"]
        read_only_fields = ["id", "created_by", "created_at"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Namespace name cannot be empty.")
        if len(value) < 3:
            raise serializers.ValidationError("Namespace name must be at least 3 characters long.")
        if len(value) > 50:
            raise serializers.ValidationError("Namespace name cannot exceed 50 characters.")
        if Namespace.objects.filter(name=value).exists():
            raise serializers.ValidationError("Namespace name must be globally unique.")
        return value

    # Automatically set created_by user
    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class ShortURLSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShortURL
        fields = [
            "id", "namespace", "short_code", "original_url", 
            "created_by", "click_count", "expiry_date", 
            "is_private", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_by", "click_count", "created_at", "updated_at"]

    # Validate original_url
    def validate_original_url(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Original URL cannot be empty.")
        return value

    # Validate short_code
    def validate_short_code(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Short code cannot be empty.")
        if len(value) < 3:
            raise serializers.ValidationError("Short code must be at least 3 characters long.")
        if len(value) > 50:
            raise serializers.ValidationError("Short code cannot exceed 50 characters.")
        return value

    # Ensure unique short_code per namespace
    def validate(self, attrs):
        namespace = attrs.get("namespace")
        short_code = attrs.get("short_code")
        if ShortURL.objects.filter(namespace=namespace, short_code=short_code).exists():
            raise serializers.ValidationError("This short code already exists in the namespace.")
        return attrs

    # Automatically assign created_by
    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
