from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render

def mockup_signup(request):
    print("Mockup signup view visited!")
    return HttpResponseRedirect(reverse('login'))

def menu(request):
    return render(request,"menu.html")

def profile(request):
    return render(request,"profile.html")