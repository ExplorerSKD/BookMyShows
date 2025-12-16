from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile


class UserRegistrationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[
            (UserProfile.ROLE_CUSTOMER, 'Customer / User'),
            (UserProfile.ROLE_ORGANIZER, 'Organizer / Venue (requires approval)'),
            (UserProfile.ROLE_STAFF, 'Staff / Gate Scanner (requires approval)'),
        ],
        label='Account Type',
        widget=forms.RadioSelect,
        initial=UserProfile.ROLE_CUSTOMER,
    )

    email = forms.EmailField(required=True, help_text='Required. A valid email address.')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role')


from .models import Movie

class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = ['title', 'description', 'duration_mins', 'language', 'genre', 'poster_url', 'trailer_url']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

