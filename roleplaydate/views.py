from django.http import HttpResponseRedirect
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse
from django.shortcuts import render
from accounts.forms import EditProfileForm

def mockup_signup(request):
    print("Mockup signup view visited!")
    return HttpResponseRedirect(reverse('login'))

def menu(request):
    return render(request,"menu.html")

def edit_profile(request):
    form = EditProfileForm()
    return render(request, 'edit_profile.html', {'form': form})