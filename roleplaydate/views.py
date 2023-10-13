from django.http import HttpResponseRedirect
from django.urls import reverse

def mockup_signup(request):
    print("Mockup signup view visited!")
    return HttpResponseRedirect(reverse('login'))