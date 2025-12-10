"""
API views for JWT authentication and user management
"""
import logging
import os
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.core.response import success_response, error_response
from apps.core.permissions import IsProducer, IsBuyer
from apps.notifications.emails import send_password_reset_email
from .models import User
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    OnboardingProducerSerializer,
    OnboardingBuyerSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)

logger = logging.getLogger(__name__)


@extend_schema(tags=['Authentication'])
class RegisterView(APIView):
    """User registration endpoint"""
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(description='User registered successfully'),
            400: OpenApiResponse(description='Validation error')
        }
    )
    def post(self, request):
        """Register a new user (producer or buyer)"""
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            user_data = UserSerializer(user).data

            return success_response(
                data=user_data,
                message="User registered successfully. Please complete onboarding.",
                status_code=status.HTTP_201_CREATED
            )

        return error_response(
            message="Registration failed.",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(tags=['Authentication'])
class LoginView(APIView):
    """User login endpoint with JWT tokens"""
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description='Login successful'),
            400: OpenApiResponse(description='Invalid credentials')
        }
    )
    def post(self, request):
        """Login with username/email and password"""
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = serializer.validated_data['tokens']
            user_data = UserSerializer(user).data

            return success_response(
                data={
                    'user': user_data,
                    'tokens': tokens
                },
                message="Login successful."
            )

        return error_response(
            message="Login failed.",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(tags=['Authentication'])
class ProfileView(APIView):
    """User profile view and update"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: UserSerializer
        }
    )
    def get(self, request):
        """Get current user profile"""
        serializer = UserSerializer(request.user)
        return success_response(
            data=serializer.data,
            message="Profile retrieved successfully."
        )

    @extend_schema(
        request=UserSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description='Validation error')
        }
    )
    def patch(self, request):
        """Update user profile (limited fields)"""
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return success_response(
                data=serializer.data,
                message="Profile updated successfully."
            )

        return error_response(
            message="Profile update failed.",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(tags=['Onboarding'])
class OnboardingProducerView(APIView):
    """Producer onboarding endpoint"""
    permission_classes = [IsAuthenticated, IsProducer]

    @extend_schema(
        request=OnboardingProducerSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description='Validation error')
        }
    )
    def post(self, request):
        """Complete producer onboarding"""
        serializer = OnboardingProducerSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            user = serializer.save()
            user_data = UserSerializer(user).data

            return success_response(
                data=user_data,
                message="Producer onboarding completed successfully."
            )

        return error_response(
            message="Onboarding failed.",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(tags=['Onboarding'])
class OnboardingBuyerView(APIView):
    """Buyer onboarding endpoint"""
    permission_classes = [IsAuthenticated, IsBuyer]

    @extend_schema(
        request=OnboardingBuyerSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description='Validation error')
        }
    )
    def post(self, request):
        """Complete buyer onboarding"""
        serializer = OnboardingBuyerSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            user = serializer.save()
            user_data = UserSerializer(user).data

            return success_response(
                data=user_data,
                message="Buyer onboarding completed successfully."
            )

        return error_response(
            message="Onboarding failed.",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(tags=['Authentication'])
class ChangePasswordView(APIView):
    """Change password endpoint"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description='Password changed successfully'),
            400: OpenApiResponse(description='Validation error')
        }
    )
    def post(self, request):
        """Change user password"""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return success_response(
                message="Password changed successfully."
            )

        return error_response(
            message="Password change failed.",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(tags=['Authentication'])
class LogoutView(APIView):
    """Logout endpoint (client should discard tokens)"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(description='Logout successful')
        }
    )
    def post(self, request):
        """Logout user (token blacklisting handled by client)"""
        return success_response(
            message="Logout successful. Please discard your tokens."
        )


@extend_schema(tags=['Authentication'])
class PasswordResetRequestView(APIView):
    """Request password reset email"""
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    @extend_schema(
        request=PasswordResetRequestSerializer,
        responses={
            200: OpenApiResponse(description='Password reset email sent (or email does not exist)'),
            400: OpenApiResponse(description='Validation error')
        }
    )
    def post(self, request):
        """Send password reset email if user exists"""
        print("=" * 80)
        print("PASSWORD RESET REQUEST RECEIVED")
        print(f"Request data: {request.data}")

        serializer = PasswordResetRequestSerializer(data=request.data)

        if not serializer.is_valid():
            print(f"✗ Validation failed: {serializer.errors}")
            return error_response(
                message="Invalid email format.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        print(f"Email to reset: {email}")

        # Always return success to prevent user enumeration
        try:
            user = User.objects.get(email__iexact=email, is_active=True)
            print(f"✓ User found: {user.username} (ID: {user.id})")

            # Generate token
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Build reset URL
            frontend_url = os.getenv('FRONTEND_URL', request.build_absolute_uri('/'))
            reset_url = f"{frontend_url.rstrip('/')}/reset-password?uid={uid}&token={token}"

            # Send email (with error handling)
            try:
                send_password_reset_email(user, reset_url)
                print(f"✓ Password reset email sent to {email}")
                logger.info(f"Password reset email sent to {email}")
            except Exception as e:
                print(f"✗ FAILED to send password reset email to {email}")
                print(f"✗ Error: {str(e)}")
                print(f"✗ Error type: {type(e).__name__}")
                import traceback
                print(traceback.format_exc())
                logger.error(f"Failed to send password reset email to {email}: {str(e)}")
                # Don't raise - still return success to prevent user enumeration

        except User.DoesNotExist:
            # Log but don't reveal user doesn't exist
            print(f"✗ User not found for email: {email}")
            logger.info(f"Password reset requested for non-existent email: {email}")

        print("Returning success response")
        print("=" * 80)
        return success_response(
            data={},
            message="If the email exists, a reset link has been sent."
        )


@extend_schema(tags=['Authentication'])
class PasswordResetConfirmView(APIView):
    """Confirm password reset with token"""
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    @extend_schema(
        request=PasswordResetConfirmSerializer,
        responses={
            200: OpenApiResponse(description='Password reset successful'),
            400: OpenApiResponse(description='Validation error or invalid token')
        }
    )
    def post(self, request):
        """Reset password with valid token"""
        serializer = PasswordResetConfirmSerializer(data=request.data)

        if serializer.is_valid():
            result = serializer.save()
            user_data = UserSerializer(result['user']).data

            return success_response(
                data={
                    'user': user_data,
                    'tokens': result['tokens']
                },
                message="Password has been reset successfully."
            )

        return error_response(
            message="Password reset failed.",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
