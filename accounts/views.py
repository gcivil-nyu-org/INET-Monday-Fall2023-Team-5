from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import EditProfileForm


class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

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

