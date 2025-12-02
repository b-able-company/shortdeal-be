from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignUpForm, LoginForm, ProducerOnboardingForm, BuyerOnboardingForm, ProfileUpdateForm, PasswordChangeForm


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
