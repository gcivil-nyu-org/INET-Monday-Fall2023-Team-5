from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import EditProfileForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from .forms import CustomUserCreationForm
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site


class SignUpView(generic.CreateView):
    form_class = CustomUserCreationForm
    # success_url = reverse_lazy("profile-create")
    success_url = reverse_lazy("confirmation_required")
    template_name = "registration/signup.html"

    def form_valid(self, form):
        # Save the user but set it to inactive
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        # Generate token and uid for confirmation email
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        confirmation_link  = f'http://127.0.0.1:8000/accounts/confirm/{uid}/{token}/'


        # Send the confirmation email
        send_mail(
            'Confirm your registration',
            f'Click the link to confirm: {confirmation_link}',
            'from@example.com',
            [user.email],
            fail_silently=False,
        )

        messages.success(self.request, "Please confirm your email to complete the registration.")
        return super().form_valid(form)
    
@login_required
def edit_profile(request):
    profile = request.user.profile  # refers to the currently authenticated user

    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile.open_to_dating = form.cleaned_data['open_to_dating']
            profile.pronoun_preference = form.cleaned_data['pronoun_preference']
            pronoun_preference = form.cleaned_data['pronoun_preference']
            if pronoun_preference == 'other':
                profile.pronoun_preference = form.cleaned_data['custom_pronoun']
            else:
                profile.pronoun_preference = pronoun_preference
            profile.save()
            updated_user = request.user
            updated_pronoun_preference = profile.get_pronoun_preference_display()
            return HttpResponseRedirect(reverse('profile_updated'))
            #return render(request, 'profile_updated.html', {'user': updated_user, 'pronoun_preference': updated_pronoun_preference})

    else:
        form = EditProfileForm(instance=profile)
        return render(request, 'edit_profile.html', {'form': form})

    pronoun_preference = profile.get_pronoun_preference_display()
    return render(request, 'home.html', {'user': request.user, 'pronoun_preference': pronoun_preference, 'form': form})


def profile_updated(request):
    profile = request.user.profile
    updated_pronoun_preference = profile.get_pronoun_preference_display()

    return render(request, 'profile_updated.html',
                  {'user': request.user, 'pronoun_preference': updated_pronoun_preference})


def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.profile.is_confirmed = True  # Set the profile confirmed attribute to True
        user.save()
        messages.success(request, "Your account has been activated. You can now login.")
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid!')
        return redirect('home')

def confirmation_required(request):
    return render(request, 'registration/confirmation_required.html')