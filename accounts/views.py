from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views import generic
from django.shortcuts import render
from django.contrib import messages
from .forms import EditProfileForm
from .models import User, Like, Profile, Match

# from django.core.paginator import Paginator
from django.contrib.auth.tokens import default_token_generator
from .forms import CustomUserCreationForm
from django.utils.http import urlsafe_base64_decode
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q


class SignUpView(generic.CreateView):
    form_class = CustomUserCreationForm
    template_name = "accounts/registration/signup.html"
    success_url = reverse_lazy("confirmation_required")

    def get_form_kwargs(self):
        # This method provides arguments for form instantiation.
        # We'll override it to include the domain.
        kwargs = super(SignUpView, self).get_form_kwargs()
        kwargs["domain"] = self.request.get_host()
        return kwargs

    def form_valid(self, form):
        messages.success(
            self.request, "Please confirm your email to complete the registration."
        )
        return super().form_valid(form)


def home(request):
    return render(request, "home.html")


def about(request):
    return render(request, "accounts/about.html", {"title": "About"})


@login_required
def edit_profile(request):
    profile = request.user.profile  # refers to the currently authenticated user

    if request.method == "POST":
        form = EditProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            _handle_form_valid(request, form)
            return HttpResponseRedirect(reverse("profile_updated"))
        else:
            messages.error(
                request, "There was an error in the form. Please check your inputs."
            )
    else:
        form = EditProfileForm(instance=profile)

    return render(request, "accounts/profile/edit_profile.html", {"form": form})


def _handle_form_valid(request, form):
    """Helper function to process a valid form submission."""
    # Get the data but do not save it immediately
    profile_instance = form.save(commit=False)

    pronoun_preference = form.cleaned_data["pronoun_preference"]
    custom_pronoun = form.cleaned_data.get("custom_pronoun")

    if pronoun_preference == "other" and custom_pronoun:
        profile_instance.pronoun_preference = custom_pronoun
        profile_instance.custom_pronoun = custom_pronoun
    else:
        profile_instance.pronoun_preference = pronoun_preference

    # Handle profile picture: clear it if the 'clear' checkbox is selected;
    # otherwise, check for an uploaded image

    if form.cleaned_data.get(
        "profile_picture-clear"
    ):  # Note the change in the field name to match Django's default
        profile_instance.profile_picture = ""
    elif request.FILES.get(
        "profile_picture"
    ):  # More Pythonic way to handle file uploads
        profile_instance.profile_picture = request.FILES["profile_picture"]

    # Save the profile instance now
    profile_instance.save()

    # Handling the ManyToMany field
    open_to_dating_choices = form.cleaned_data.get("open_to_dating")
    if open_to_dating_choices:
        profile_instance.open_to_dating.set(open_to_dating_choices)


def profile_updated(request):
    profile = request.user.profile
    updated_pronoun_preference = profile.get_pronoun_preference_display()

    return render(
        request,
        "accounts/profile/profile_updated.html",
        {"user": request.user, "pronoun_preference": updated_pronoun_preference},
    )


@login_required
def view_profile(request):
    profile = request.user.profile
    pronoun_preference = profile.get_pronoun_preference_display()

    # Fetching dating preferences
    open_to_dating = profile.open_to_dating.all()
    return render(
        request,
        "accounts/profile/view_profile.html",
        {
            "user": request.user,
            "profile": profile,
            "pronoun_preference": pronoun_preference,
            "open_to_dating": open_to_dating,
        },
    )


@login_required
def browse_profiles(request):
    recommended_profiles = get_recommended_profiles(request.user).order_by("user_id")

    # Pagination: Show 10 profiles per page
    # paginator = Paginator(recommended_profiles, 10)
    # page = request.GET.get("page")
    # profiles = paginator.get_page(page)

    return render(
        request,
        "accounts/profile/browse_profiles.html",
        {"profiles": recommended_profiles},
    )


@login_required
def view_single_profile(request, profile_id):
    profile = get_object_or_404(Profile, pk=profile_id)

    # Check if the current user has already liked this profile.
    has_liked = False
    if request.user.is_authenticated:
        has_liked = Like.objects.filter(
            from_user=request.user, to_user=profile.user
        ).exists()

    # Prepare context data for template
    context = {
        "profile": profile,
        "has_liked": has_liked,
    }

    return render(request, "accounts/profile/single_profile.html", context)


def get_recommended_profiles(user):
    user_profile = user.profile
    user_gender = user_profile.gender
    user_open_to_dating = user_profile.open_to_dating.values_list("gender", flat=True)

    # Profiles that match the user's dating preferences
    matching_gender_profiles = Profile.objects.filter(gender__in=user_open_to_dating)

    # Of those, which are open to dating someone of the user's gender
    recommended_profiles = matching_gender_profiles.filter(
        open_to_dating__gender__in=[user_gender]
    )

    # Exclude the current user's profile from the recommended list
    recommended_profiles = recommended_profiles.exclude(user=user)

    return recommended_profiles


def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.profile.is_confirmed = True  # Set the profile confirmed attribute to True
        user.save()
        messages.success(request, "Your account has been activated. You can now login.")
        return redirect("login")
    else:
        messages.error(request, "Activation link is invalid!")
        return redirect("home")


def confirmation_required(request):
    return render(request, "accounts/registration/confirmation_required.html")


@login_required
def account(request):
    if request.method == "POST":
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(
                request, user
            )  # Important, to keep the user logged in after password change
            return JsonResponse(
                {"status": "success", "message": "Password updated successfully"},
                status=200,
            )
        else:
            # Here we create a list of error messages
            errors = [
                f"{field}: {error[0]}" for field, error in password_form.errors.items()
            ]
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Some errors occurred:",
                    "errors": errors,
                },
                status=400,
            )
    else:
        password_form = PasswordChangeForm(request.user)

    return render(request, "accounts/account.html", {"password_form": password_form})


@login_required
def like_profile(request, user_id):
    if request.method == "POST":
        receiving_user = get_object_or_404(User, pk=user_id)
        current_user_profile = request.user.profile
        existing_like = Like.objects.filter(
            from_user=request.user, to_user=receiving_user
        ).first()

        # Check if the user has already liked this profile
        if existing_like:
            return JsonResponse(
                {"success": False, "error": "You have already liked this user."},
                status=200,
            )

        # Check if the user has no likes remaining
        if current_user_profile.likes_remaining <= 0:
            return JsonResponse(
                {"success": False, "error": "You have reached your daily likes limit"},
                status=200,
            )

        # Proceed to create a new like
        Like.objects.create(from_user=request.user, to_user=receiving_user)
        current_user_profile.likes_remaining -= 1
        current_user_profile.save()

        # Check for mutual like
        mutual_like = Like.objects.filter(
            from_user=receiving_user, to_user=request.user
        ).exists()

        # Check if either user is already matched
        user_already_matched = Match.objects.filter(
            Q(user1=request.user)
            | Q(user2=request.user)
            | Q(user1=receiving_user)
            | Q(user2=receiving_user)
        ).exists()

        if mutual_like and not user_already_matched:
            # Create a match
            Match.objects.create(user1=request.user, user2=receiving_user)
            # You can add any notification logic here if needed

        return JsonResponse(
            {
                "success": True,
                "likes_remaining": current_user_profile.likes_remaining,
                "action": "liked",
                "match_created": mutual_like and not user_already_matched,
            },
            status=200,
        )

    # If the request method is not POST, return an error
    return JsonResponse(
        {"success": False, "error": "Invalid request method."}, status=405
    )
