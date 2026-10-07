import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import EmailVerificationToken, User
from .serializers import (
    EmailVerificationSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegistrationSerializer,
    UserSerializer,
)


def _send_verification_email(user):
    raw_token = secrets.token_urlsafe(32)
    EmailVerificationToken.objects.filter(user=user, used_at__isnull=True).update(
        used_at=timezone.now()
    )
    EmailVerificationToken.objects.create(
        user=user,
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        expires_at=timezone.now() + timedelta(hours=24),
    )
    send_mail(
        "Verify your RMI email address",
        f"Use this verification token to verify your account: {raw_token}",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )


@extend_schema(
    tags=["accounts"],
    request=RegistrationSerializer,
    responses={201: UserSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    _send_verification_email(user)
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["accounts"],
    request=LoginSerializer,
    responses={200: UserSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]
    login(request, user)
    return Response(UserSerializer(user).data)


@extend_schema(tags=["accounts"], responses={204: None})
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["accounts"], responses=UserSerializer)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)


@extend_schema(
    tags=["accounts"],
    request=EmailVerificationSerializer,
    responses={200: UserSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def verify_email(request):
    serializer = EmailVerificationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    token_hash = hashlib.sha256(serializer.validated_data["token"].encode()).hexdigest()
    try:
        verification = EmailVerificationToken.objects.select_related("user").get(
            token_hash=token_hash
        )
    except EmailVerificationToken.DoesNotExist:
        raise ValidationError({"token": "This verification token is invalid."}) from None
    if not verification.is_valid:
        raise ValidationError({"token": "This verification token is invalid or expired."})
    verification.used_at = timezone.now()
    verification.save(update_fields=["used_at", "updated_at"])
    verification.user.mark_email_verified()
    return Response(UserSerializer(verification.user).data)


@extend_schema(
    tags=["accounts"],
    request=PasswordResetRequestSerializer,
    responses={200: dict},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = User.objects.filter(
        email=serializer.validated_data["email"].lower().strip(),
        is_active=True,
    ).first()
    if user:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        send_mail(
            "Reset your RMI password",
            f"Use this reset link: {settings.FRONTEND_URL}/reset-password/{uid}/{token}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
    return Response({"message": "If an account exists, reset instructions have been sent."})


@extend_schema(
    tags=["accounts"],
    request=PasswordResetConfirmSerializer,
    responses={200: dict},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]
    user.set_password(serializer.validated_data["new_password"])
    user.save(update_fields=["password", "updated_at"])
    return Response({"message": "Your password has been reset."})
