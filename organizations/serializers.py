from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django.utils import timezone
from hirethon_template.users.models import User,Organization,Membership,Invite,Namespace,ShortURL
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
        
        if not re.match(r'^[\w\s-]+$', value):
            raise serializers.ValidationError("Organization name contains invalid characters.")

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
    """
    Handles both:
      - Creating new invitations (by admin)
      - Accepting/Rejecting invitations (by invited user)
    """

    action = serializers.CharField(write_only=True, required=False)  # for 'accept' or 'reject'

    class Meta:
        model = Invite
        fields = [
            "id", "organization", "email", "role",
            "status", "token", "created_at", "accepted_at", "expires_at", "action"
        ]
        read_only_fields = ["id", "status", "token", "created_at", "accepted_at", "expires_at"]


    def validate_email(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Email cannot be empty.")
        org = self.context.get("organization")
        if Invite.objects.filter(email=value, organization=org, status="Pending").exists():
            raise serializers.ValidationError("A pending invite already exists for this email.")
        return value

    def validate_role(self, value):
        if value not in dict(Membership.ROLE_CHOICES):
            raise serializers.ValidationError("Invalid role. Must be Admin, Editor, or Viewer.")
        return value

    def validate(self, attrs):
        """
        Handle both invite creation & action updates.
        """
        # Handle accept/reject case (token already in context)
        invite = self.context.get("invite")

        # Case 1 → Action (accept/reject)
        if invite:
            action = attrs.get("action")

            if not action:
                raise serializers.ValidationError({"action": "Action ('accept' or 'reject') is required."})

            # Check expiry
            if invite.is_expired():
                invite.status = "Expired"
                invite.save()
                raise serializers.ValidationError("This invite has expired.")

            # Prevent re-using same invite
            if invite.status in ["Accepted", "Rejected"]:
                raise serializers.ValidationError(f"This invite was already {invite.status.lower()}.")

            if action not in ["accept", "reject"]:
                raise serializers.ValidationError("Invalid action. Must be 'accept' or 'reject'.")

        # Case 2 → Creation (no invite yet)
        else:
            org = self.context.get("organization")
            email = attrs.get("email")

            if not org:
                raise serializers.ValidationError("Organization context is required for creating an invite.")

            # Check for duplicate pending invites
            if Invite.objects.filter(email=email, organization=org, status="Pending").exists():
                raise serializers.ValidationError("A pending invite already exists for this email.")

        return attrs


    def create(self, validated_data):
        """
        Create a new invite with a token and expiry.
        """
        validated_data["token"] = uuid.uuid4()
        validated_data["expires_at"] = timezone.now() + timezone.timedelta(days=3)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Process invite acceptance or rejection.
        """
        user = self.context.get("user")
        action = validated_data.get("action")

        if action == "accept":
            # Prevent duplicate membership
            if Membership.objects.filter(user=user, organization=instance.organization).exists():
                raise serializers.ValidationError("You are already a member of this organization.")

            # Create membership
            Membership.objects.create(
                user=user,
                organization=instance.organization,
                role=instance.role
            )

            instance.status = "Accepted"
            instance.accepted_at = timezone.now()
            instance.save()
            return instance

        elif action == "reject":
            instance.status = "Rejected"
            instance.save()
            return instance

        else:
            raise serializers.ValidationError("Invalid action. Must be 'accept' or 'reject'.")
