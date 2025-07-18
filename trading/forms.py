from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    pan_image = forms.ImageField(required=True, label='PAN Card Image')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'pan_image']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(user=user, pan_image=self.cleaned_data['pan_image'])
        return user