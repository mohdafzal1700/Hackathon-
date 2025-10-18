from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from hirethon_template.users.models import User,Organization,Membership,Invite,Namespace,ShortURL
import string, random
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
        if not re.match(r'^[\w-]+$', value):
            raise serializers.ValidationError("Namespace name can only contain letters, numbers, hyphens, and underscores.")
        if len(value) > 50:
            raise serializers.ValidationError("Namespace name cannot exceed 50 characters.")
        if Namespace.objects.filter(name=value).exists():
            raise serializers.ValidationError("Namespace name must be globally unique.")
        return value

    # Automatically set created_by user
    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
    

def generate_unique_short_code(namespace, length=6):
    """Generate a unique short code within the namespace."""
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        if not ShortURL.objects.filter(namespace=namespace, short_code=code).exists():
            return code
        
class ShortURLSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShortURL
        fields = [
            "id", "namespace", "short_code", "original_url",
            "created_by", "click_count", "expiry_date",
            "is_private", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_by", "click_count", "created_at", "updated_at"]

    def validate_original_url(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Original URL cannot be empty.")
        return value

    def validate_short_code(self, value):
        if value:
            value = value.strip()
            if len(value) < 3:
                raise serializers.ValidationError("Short code must be at least 3 characters long.")
            if len(value) > 50:
                raise serializers.ValidationError("Short code cannot exceed 50 characters.")
        return value

    def validate(self, attrs):
        namespace = attrs.get("namespace")
        short_code = attrs.get("short_code")

        # Generate a unique short code if none is provided
        if not short_code:
            attrs["short_code"] = generate_unique_short_code(namespace)
        else:
            if ShortURL.objects.filter(namespace=namespace, short_code=short_code).exists():
                raise serializers.ValidationError("This short code already exists in the namespace.")

        return attrs

    def create(self, validated_data):
        # Assign the creator
        validated_data["created_by"] = self.context["request"].user
        # Now call the parent method to save
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Update only provided fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
