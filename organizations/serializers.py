from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from .models import User,Organization,Membership,Invite,Namespace,ShortURL
import re
import logging 
import uuid


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
