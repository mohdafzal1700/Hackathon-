from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from .models import User,Organization,Membership,Invite,Namespace,ShortURL
import re
import logging 
import uuid


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        org = Organization.objects.create(name=f"{user.username}'s Org")
        Membership.objects.create(user=user, organization=org, role="Admin")
        return user    


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model=Organization
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        
    def validate_name(self, value):
        # Strip leading/trailing spaces
        value = value.strip()

        # Check empty string
        if not value:
            raise serializers.ValidationError("Organization name cannot be empty.")

        # Check minimum length
        if len(value) < 4:
            raise serializers.ValidationError("Organization name must be at least 4 characters long.")

        # Check maximum length (optional)
        if len(value) > 50:
            raise serializers.ValidationError("Organization name cannot exceed 50 characters.")

        # Check uniqueness
        if Organization.objects.filter(name=value).exists():
            raise serializers.ValidationError("Organization name already exists.")

        return value


class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ["id", "user", "organization", "role", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_role(self, value):
        if value not in dict(Membership.ROLE_CHOICES):
            raise serializers.ValidationError("Invalid role. Must be Admin, Editor, or Viewer.")
        return value

    def validate(self, attrs):
        user = attrs.get("user")
        org = attrs.get("organization")

        if Membership.objects.filter(user=user, organization=org).exists():
            raise serializers.ValidationError("This user already has a role in this organization.")
        return attrs


class InviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invite
        fields = ["id", "organization", "email", "role", "status", "token", "created_at", "accepted_at"]
        read_only_fields = ["id", "status", "token", "created_at", "accepted_at"]

    # Validate email
    def validate_email(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Email cannot be empty.")
        if Invite.objects.filter(email=value, organization=self.context.get("organization")).exists():
            raise serializers.ValidationError("An invite has already been sent to this email.")
        return value

    # Validate role
    def validate_role(self, value):
        if value not in dict(Membership.ROLE_CHOICES):
            raise serializers.ValidationError("Invalid role. Must be Admin, Editor, or Viewer.")
        return value

    # Create method to auto-generate token
    def create(self, validated_data):
        validated_data["token"] = uuid.uuid4()
        return super().create(validated_data)



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
