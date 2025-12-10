"""
Serializers for JWT authentication and user management
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from apps.core.validators import validate_genre_tags


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    role = serializers.ChoiceField(
        choices=[
            (User.Role.CREATOR, 'Producer'),
            (User.Role.BUYER, 'Buyer'),
        ],
        required=True
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'role')
        extra_kwargs = {
            'email': {'required': True}
        }

    def validate_email(self, value):
        """Check if email already exists"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        """Create new user"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login with JWT tokens"""

    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Authenticate user and return tokens"""
        username = attrs.get('username')
        password = attrs.get('password')

        # Try to authenticate with username or email
        user = authenticate(username=username, password=password)

        if not user:
            # Try with email
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass

        if not user:
            raise serializers.ValidationError("Invalid credentials.")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        attrs['user'] = user
        attrs['tokens'] = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        return attrs


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'role',
            'is_onboarded', 'company_name', 'logo', 'country',
            'genre_tags', 'booth_slug', 'phone',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'role', 'booth_slug', 'created_at', 'updated_at')


class OnboardingProducerSerializer(serializers.ModelSerializer):
    """Serializer for producer onboarding"""

    class Meta:
        model = User
        fields = ('company_name', 'logo', 'country', 'genre_tags')

    def validate_genre_tags(self, value):
        """Validate genre tags (1-3 required)"""
        return validate_genre_tags(value)

    def validate(self, attrs):
        """Check if user is a producer"""
        user = self.context['request'].user

        if user.role != User.Role.CREATOR:
            raise serializers.ValidationError("Only producers can complete producer onboarding.")

        if user.is_onboarded:
            raise serializers.ValidationError("Onboarding already completed.")

        return attrs

    def update(self, instance, validated_data):
        """Update user and mark as onboarded"""
        instance.company_name = validated_data.get('company_name', instance.company_name)
        instance.country = validated_data.get('country', instance.country)
        instance.genre_tags = validated_data.get('genre_tags', instance.genre_tags)

        if 'logo' in validated_data:
            instance.logo = validated_data['logo']

        instance.is_onboarded = True
        instance.save()

        return instance


class OnboardingBuyerSerializer(serializers.ModelSerializer):
    """Serializer for buyer onboarding"""

    class Meta:
        model = User
        fields = ('company_name', 'country')

    def validate(self, attrs):
        """Check if user is a buyer"""
        user = self.context['request'].user

        if user.role != User.Role.BUYER:
            raise serializers.ValidationError("Only buyers can complete buyer onboarding.")

        if user.is_onboarded:
            raise serializers.ValidationError("Onboarding already completed.")

        return attrs

    def update(self, instance, validated_data):
        """Update user and mark as onboarded"""
        instance.company_name = validated_data.get('company_name', instance.company_name)
        instance.country = validated_data.get('country', instance.country)
        instance.is_onboarded = True
        instance.save()

        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change"""

    current_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate_current_password(self, value):
        """Check if current password is correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        """Validate new password confirmation"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        return attrs

    def save(self):
        """Update user password"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Normalize email to lowercase for consistent lookup"""
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""

    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Validate token and password confirmation"""
        # Check password match
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})

        # Decode uid and get user
        try:
            uid = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"uid": "Invalid user ID."})

        # Validate token
        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError({"token": "Invalid or expired token."})

        attrs['user'] = user
        return attrs

    def save(self):
        """Update user password and optionally return tokens"""
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()

        # Return fresh JWT tokens for auto-login
        refresh = RefreshToken.for_user(user)
        return {
            'user': user,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }
