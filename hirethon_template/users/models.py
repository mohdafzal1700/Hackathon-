from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid


# 0️⃣ Custom User Manager
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # hash password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


#  User
class User(AbstractUser):
    username = None  # Not used
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


#  Organization
class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organizations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


#  Membership / Role
class Membership(models.Model):
    ROLE_CHOICES = [
        ("Admin", "Admin"),
        ("Editor", "Editor"),
        ("Viewer", "Viewer"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="members")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "organization")  # a user has only one role per org

    def __str__(self):
        return f"{self.user.email} - {self.role} in {self.organization.name}"


#  Invite
class Invite(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Accepted", "Accepted"),
        ("Rejected", "Rejected"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="invites")
    email = models.EmailField()
    role = models.CharField(max_length=10, choices=Membership.ROLE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Pending")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)  # auto-generate token
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Invite for {self.email} to {self.organization.name}"


#  Namespace
class Namespace(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="namespaces")
    name = models.CharField(max_length=255, unique=True)  # globally unique
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_namespaces")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.organization.name} / {self.name}"


# ShortURL
class ShortURL(models.Model):
    namespace = models.ForeignKey(Namespace, on_delete=models.CASCADE, related_name="shorturls")
    short_code = models.CharField(max_length=50)  # unique per namespace
    original_url = models.URLField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_shorturls")
    click_count = models.PositiveIntegerField(default=0)
    expiry_date = models.DateTimeField(null=True, blank=True)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("namespace", "short_code")  # ensures shortcode unique per namespace

    def __str__(self):
        return f"{self.namespace.name}/{self.short_code} → {self.original_url}"
