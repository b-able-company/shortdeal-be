from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignUpForm, LoginForm


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

            # Redirect based on role
            if user.role == 'creator':
                return redirect('accounts:profile')
            elif user.role == 'buyer':
                return redirect('accounts:profile')
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
    return render(request, 'accounts/profile.html', {
        'user': request.user
    })
