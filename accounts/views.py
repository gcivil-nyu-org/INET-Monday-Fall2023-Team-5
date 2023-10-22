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
from django.core.paginator import Paginatorfrom
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
    template_name = "registration/signup.html"
    success_url = reverse_lazy("confirmation_required")

    def form_valid(self, form):
        # Save the user but set it to inactive
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        # Generate token and uid for confirmation email
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        confirmation_link = f'http://127.0.0.1:8000/accounts/confirm/{uid}/{token}/'

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

    # Handle profile picture upload
    if 'profile_picture' in request.FILES:
        profile_instance.profile_picture = request.FILES['profile_picture']

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
        'profile': profile,
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