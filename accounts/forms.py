from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    birth_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    gender = forms.ChoiceField(choices=User.GENDER_CHOICES)
    looking_for = forms.ChoiceField(choices=User.GENDER_CHOICES)
    bio = forms.CharField(widget=forms.Textarea, required=False)
    location = forms.CharField(max_length=100, required=False)
    profile_picture = forms.ImageField(required=False)
    latitude = forms.DecimalField(max_digits=9, decimal_places=6, required=False, widget=forms.HiddenInput())
    longitude = forms.DecimalField(max_digits=9, decimal_places=6, required=False, widget=forms.HiddenInput())

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'birth_date', 
                 'gender', 'looking_for', 'bio', 'location', 'profile_picture',
                 'latitude', 'longitude')

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('bio', 'location', 'profile_picture', 'looking_for', 'latitude', 'longitude')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'looking_for': forms.Select(attrs={'class': 'form-select'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        } 