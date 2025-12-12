from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User


class SignUpForm(UserCreationForm):
    """Role-based signup form"""

    email = forms.EmailField(
        max_length=255,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address'
        })
    )

    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )

    role = forms.ChoiceField(
        choices=[
            (User.Role.CREATOR, 'Producer'),
            (User.Role.BUYER, 'Buyer'),
        ],  # Admin users created via Django admin only
        required=True,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Select your role'
    )

    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password (minimum 8 characters)'
        })
    )

    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already in use.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """Login form"""

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or email'
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


class ProducerOnboardingForm(forms.ModelForm):
    """Producer onboarding form with company profile"""

    GENRE_CHOICES = [
        ('drama', 'Drama'),
        ('comedy', 'Comedy'),
        ('romance', 'Romance'),
        ('action', 'Action'),
        ('thriller', 'Thriller'),
        ('horror', 'Horror'),
        ('documentary', 'Documentary'),
        ('education', 'Education'),
        ('business', 'Business'),
        ('lifestyle', 'Lifestyle'),
        ('food', 'Food'),
        ('travel', 'Travel'),
        ('music', 'Music'),
        ('sports', 'Sports'),
        ('gaming', 'Gaming'),
    ]

    company_name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your company name'
        }),
        label='Company Name'
    )

    logo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        label='Company Logo',
        help_text='Upload your company logo (JPG or PNG, max 2MB)'
    )

    country = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your country'
        }),
        label='Country'
    )

    genre_tags = forms.MultipleChoiceField(
        choices=GENRE_CHOICES,
        required=True,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Select Genres (up to 3)',
        help_text='Choose 1-3 genres that best describe your content'
    )

    class Meta:
        model = User
        fields = ('company_name', 'logo', 'country', 'genre_tags')

    def clean_genre_tags(self):
        genre_tags = self.cleaned_data.get('genre_tags')
        if len(genre_tags) < 1:
            raise forms.ValidationError('Please select at least 1 genre.')
        if len(genre_tags) > 3:
            raise forms.ValidationError('Please select no more than 3 genres.')
        return list(genre_tags)

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo:
            if logo.size > 2 * 1024 * 1024:  # 2MB
                raise forms.ValidationError('Logo file size must be under 2MB.')
        return logo


class BuyerOnboardingForm(forms.ModelForm):
    """Buyer onboarding form with company profile"""

    company_name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your company name'
        }),
        label='Company Name'
    )

    country = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your country'
        }),
        label='Country'
    )

    class Meta:
        model = User
        fields = ('company_name', 'country')


class ProfileUpdateForm(forms.ModelForm):
    """Profile update form for settings page"""

    GENRE_CHOICES = [
        ('drama', 'Drama'),
        ('comedy', 'Comedy'),
        ('romance', 'Romance'),
        ('action', 'Action'),
        ('thriller', 'Thriller'),
        ('horror', 'Horror'),
        ('documentary', 'Documentary'),
        ('education', 'Education'),
        ('business', 'Business'),
        ('lifestyle', 'Lifestyle'),
        ('food', 'Food'),
        ('travel', 'Travel'),
        ('music', 'Music'),
        ('sports', 'Sports'),
        ('gaming', 'Gaming'),
    ]

    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )

    email = forms.EmailField(
        max_length=255,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address'
        })
    )

    company_name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Company name'
        }),
        label='Company Name'
    )

    country = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Country'
        }),
        label='Country'
    )

    logo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        label='Company Logo',
        help_text='Upload your company logo (JPG or PNG, max 2MB)'
    )

    genre_tags = forms.MultipleChoiceField(
        choices=GENRE_CHOICES,
        required=False,  # Not required because buyers don't have it
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Select Genres (up to 3)',
        help_text='Choose 1-3 genres that best describe your content'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'company_name', 'country', 'logo', 'genre_tags')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove logo and genre_tags fields for non-creators
        if self.instance and self.instance.role != 'creator':
            self.fields.pop('logo', None)
            self.fields.pop('genre_tags', None)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This email is already in use.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo:
            if logo.size > 2 * 1024 * 1024:  # 2MB
                raise forms.ValidationError('Logo file size must be under 2MB.')
        return logo

    def clean_genre_tags(self):
        genre_tags = self.cleaned_data.get('genre_tags')
        # Only validate for creators
        if self.instance and self.instance.role == 'creator':
            if genre_tags:
                if len(genre_tags) < 1:
                    raise forms.ValidationError('Please select at least 1 genre.')
                if len(genre_tags) > 3:
                    raise forms.ValidationError('Please select no more than 3 genres.')
                return list(genre_tags)
            else:
                # If creator but no genres selected, return existing genres
                return self.instance.genre_tags if self.instance.genre_tags else []
        return genre_tags


class PasswordChangeForm(forms.Form):
    """Password change form for settings page"""

    old_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter current password'
        })
    )

    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password (minimum 8 characters)'
        }),
        min_length=8
    )

    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError('Your current password is incorrect.')
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError('The two password fields must match.')

        return cleaned_data

    def save(self):
        password = self.cleaned_data.get('new_password1')
        self.user.set_password(password)
        self.user.save()
        return self.user


class PasswordResetRequestForm(forms.Form):
    """Form for requesting password reset"""

    email = forms.EmailField(
        max_length=255,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        }),
        label='Email Address'
    )


class PasswordResetConfirmForm(forms.Form):
    """Form for confirming password reset"""

    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password (minimum 8 characters)'
        }),
        min_length=8
    )

    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        try:
            validate_password(password)
        except ValidationError as e:
            raise forms.ValidationError(e.messages)
        return password

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError('The two password fields must match.')

        return cleaned_data
