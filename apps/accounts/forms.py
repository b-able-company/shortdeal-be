from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
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
        choices=User.Role.choices,
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
