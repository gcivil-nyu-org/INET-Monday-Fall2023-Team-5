from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.urls import reverse
from django.views import generic
from django.shortcuts import render, reverse
from django.contrib import messages
from .forms import EditProfileForm
from .models import Profile
from django.core.paginator import Paginator


class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    template_name = "registration/signup.html"

    def get_success_url(self):
        return reverse('edit_profile')  # redirecting to edit_profile after successful registration

    def form_valid(self, form):
        response = super().form_valid(form)  # Call the parent class's form_valid method
        # Automatically log the user in
        new_user = authenticate(username=form.cleaned_data['username'],
                                password=form.cleaned_data['password1'])
        login(self.request, new_user)
        return response

def about(request):
    return render(request, 'about.html', {'title': 'About'})

@login_required
def edit_profile(request):
    profile = request.user.profile  # refers to the currently authenticated user

    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=profile)
        if form.is_valid():
            _handle_form_valid(request, form)
            return HttpResponseRedirect(reverse('profile_updated'))
            # return render(request, 'profile_updated.html', {'user': request.user, 'pronoun_preference': request.user.profile.get_pronoun_preference_display()})
        else:
            messages.error(request, 'There was an error in the form. Please check your inputs.')
    else:
        form = EditProfileForm(instance=profile)

    return render(request, 'profile/edit_profile.html', {'form': form})


def _handle_form_valid(request, form):
    """Helper function to process a valid form submission."""
    # Get the data but do not save it immediately
    profile_instance = form.save(commit=False)

    pronoun_preference = form.cleaned_data['pronoun_preference']
    if pronoun_preference == 'other':
        profile_instance.pronoun_preference = form.cleaned_data['custom_pronoun']
    else:
        profile_instance.pronoun_preference = pronoun_preference

    # Save the profile instance to make sure we can set many-to-many relationships
    profile_instance.save()

    # Handling the ManyToMany field
    open_to_dating_choices = form.cleaned_data['open_to_dating']
    profile_instance.open_to_dating.set(open_to_dating_choices)



def profile_updated(request):
    profile = request.user.profile
    updated_pronoun_preference = profile.get_pronoun_preference_display()

    return render(request, 'profile/profile_updated.html',
                  {'user': request.user, 'pronoun_preference': updated_pronoun_preference})


@login_required
def view_profile(request):
    profile = request.user.profile
    pronoun_preference = profile.get_pronoun_preference_display()

    # Fetching dating preferences
    open_to_dating = profile.open_to_dating.all()

    return render(request, 'profile/view_profile.html', {
        'user': request.user,
        'profile': profile,  # Add this line to pass the profile object to the template
        'pronoun_preference': pronoun_preference,
        'open_to_dating': open_to_dating
    })

@login_required
def browse_profiles(request):
    recommended_profiles = get_recommended_profiles(request.user)
    
    # Pagination: Show 10 profiles per page
    paginator = Paginator(recommended_profiles, 10)
    page = request.GET.get('page')
    profiles = paginator.get_page(page)

    return render(request, 'profile/browse_profiles.html', {'profiles': profiles})



def get_recommended_profiles(user):
    user_profile = user.profile
    user_gender = user_profile.gender
    user_open_to_dating = user_profile.open_to_dating.values_list('gender', flat=True)
    
    # Profiles that match the user's dating preferences
    matching_gender_profiles = Profile.objects.filter(gender__in=user_open_to_dating)

    # Of those, which are open to dating someone of the user's gender
    recommended_profiles = matching_gender_profiles.filter(open_to_dating__gender__in=[user_gender])
    
    # Exclude the current user's profile from the recommended list
    recommended_profiles = recommended_profiles.exclude(user=user)

    return recommended_profiles
