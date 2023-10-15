from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views import generic
from django.shortcuts import render, redirect
from .forms import EditProfileForm

class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

@login_required
def edit_profile(request):
    profile = request.user.profile  # refers to the currently authenticated user.

    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=profile)
        if form.is_valid():
            # Update the user's profile data here based on the form data
            profile.open_to_dating = form.cleaned_data['open_to_dating']
            pronoun_preference = form.cleaned_data['pronoun_preference']
            if pronoun_preference == 'other':
                profile.custom_pronoun = form.cleaned_data['custom_pronoun']
            else:
                profile.custom_pronoun = None
            profile.save()
            return redirect('profile_updated')
            # return render(request, 'profile_updated.html')
    else:
        form = EditProfileForm(instance=profile)

    # return render(request, 'profile_updated.html')
    return render(request, 'edit_profile.html', {'form': form})