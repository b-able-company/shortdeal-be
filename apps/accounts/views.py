import logging
import os
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib import messages
from .models import User
from .forms import (
    SignUpForm,
    LoginForm,
    ProducerOnboardingForm,
    BuyerOnboardingForm,
    ProfileUpdateForm,
    PasswordChangeForm,
    PasswordResetRequestForm,
    PasswordResetConfirmForm
)
from apps.notifications.emails import send_password_reset_email

logger = logging.getLogger(__name__)


def signup_view(request):
    """Role-based signup view"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Auto login after signup
            login(request, user)
            messages.success(request, f'Welcome to ShortDeal, {user.username}!')

            # Redirect to onboarding based on role
            if user.role == 'creator':
                return redirect('accounts:onboarding_producer')
            elif user.role == 'buyer':
                return redirect('accounts:onboarding_buyer')
            else:
                return redirect('home')
    else:
        form = SignUpForm()

    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    """Login view"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')

                # Redirect to next or home
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Logout view"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def profile_view(request):
    """User profile view"""
    # Redirect to onboarding if not completed
    if not request.user.is_onboarded:
        if request.user.role == 'creator':
            return redirect('accounts:onboarding_producer')
        elif request.user.role == 'buyer':
            return redirect('accounts:onboarding_buyer')

    return render(request, 'accounts/profile.html', {
        'user': request.user
    })


@login_required
def onboarding_producer_view(request):
    """Producer onboarding view"""
    # Check if already onboarded
    if request.user.is_onboarded:
        messages.info(request, 'You have already completed onboarding.')
        return redirect('accounts:profile')

    # Check if user is a producer
    if request.user.role != 'creator':
        messages.error(request, 'This page is only for producers.')
        return redirect('home')

    if request.method == 'POST':
        form = ProducerOnboardingForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_onboarded = True
            user.save()
            messages.success(request, 'Onboarding completed successfully!')
            return redirect('accounts:profile')
    else:
        form = ProducerOnboardingForm(instance=request.user)

    return render(request, 'accounts/onboarding_producer.html', {'form': form})


@login_required
def onboarding_buyer_view(request):
    """Buyer onboarding view"""
    # Check if already onboarded
    if request.user.is_onboarded:
        messages.info(request, 'You have already completed onboarding.')
        return redirect('accounts:profile')

    # Check if user is a buyer
    if request.user.role != 'buyer':
        messages.error(request, 'This page is only for buyers.')
        return redirect('home')

    if request.method == 'POST':
        form = BuyerOnboardingForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_onboarded = True
            user.save()
            messages.success(request, 'Onboarding completed successfully!')
            return redirect('accounts:profile')
    else:
        form = BuyerOnboardingForm(instance=request.user)

    return render(request, 'accounts/onboarding_buyer.html', {'form': form})


@login_required
def settings_view(request):
    """
    Settings page with profile update and password change
    Screen 18: /settings
    """
    # Redirect to onboarding if not completed
    if not request.user.is_onboarded:
        if request.user.role == 'creator':
            return redirect('accounts:onboarding_producer')
        elif request.user.role == 'buyer':
            return redirect('accounts:onboarding_buyer')

    # Handle profile update
    if request.method == 'POST' and 'action' in request.POST:
        if request.POST['action'] == 'update_profile':
            profile_form = ProfileUpdateForm(
                request.POST,
                request.FILES,
                instance=request.user
            )
            password_form = PasswordChangeForm(request.user)

            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('accounts:settings')

        elif request.POST['action'] == 'change_password':
            profile_form = ProfileUpdateForm(instance=request.user)
            password_form = PasswordChangeForm(request.user, request.POST)

            if password_form.is_valid():
                password_form.save()
                # Update session to prevent logout after password change
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully!')
                return redirect('accounts:settings')
    else:
        profile_form = ProfileUpdateForm(instance=request.user)
        password_form = PasswordChangeForm(request.user)

    return render(request, 'accounts/settings.html', {
        'profile_form': profile_form,
        'password_form': password_form,
    })


def password_reset_request_view(request):
    """Password reset request view"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        print("=" * 80)
        print("WEB PASSWORD RESET REQUEST RECEIVED")
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            print(f"Email to reset: {email}")

            # Always show success message to prevent user enumeration
            try:
                user = User.objects.get(email__iexact=email, is_active=True)
                print(f"✓ User found: {user.username} (ID: {user.id})")

                # Generate token
                token_generator = PasswordResetTokenGenerator()
                token = token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                # Build reset URL for web UI
                reset_url = request.build_absolute_uri(
                    f"/accounts/password-reset/confirm/{uid}/{token}/"
                )

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
                    # Don't raise - still show success message to user

            except User.DoesNotExist:
                print(f"✗ User not found for email: {email}")
                logger.info(f"Password reset requested for non-existent email: {email}")

            print("Redirecting with success message")
            print("=" * 80)
            messages.success(
                request,
                'If the email exists, a reset link has been sent. Please check your inbox.'
            )
            return redirect('accounts:password_reset_request')
    else:
        form = PasswordResetRequestForm()

    return render(request, 'accounts/password_reset_request.html', {'form': form})


def password_reset_confirm_view(request, uidb64, token):
    """Password reset confirm view"""
    if request.user.is_authenticated:
        return redirect('home')

    # Validate token
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    token_generator = PasswordResetTokenGenerator()

    if user is not None and token_generator.check_token(user, token):
        if request.method == 'POST':
            form = PasswordResetConfirmForm(request.POST)
            if form.is_valid():
                # Set new password
                user.set_password(form.cleaned_data['new_password1'])
                user.save()

                messages.success(
                    request,
                    'Password has been reset successfully. You can now log in with your new password.'
                )
                return redirect('accounts:login')
        else:
            form = PasswordResetConfirmForm()

        return render(request, 'accounts/password_reset_confirm.html', {
            'form': form,
            'validlink': True,
        })
    else:
        return render(request, 'accounts/password_reset_confirm.html', {
            'validlink': False,
        })
