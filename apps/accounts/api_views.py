"""
API views for JWT authentication and user management
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.core.response import success_response, error_response
from apps.core.permissions import IsProducer, IsBuyer
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    OnboardingProducerSerializer,
    OnboardingBuyerSerializer,
    ChangePasswordSerializer
)


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
