from django.shortcuts import redirect, render
#from django.contrib import auth, messages
#from django.contrib..auth.models import User


# Onboarding Splash Page
def index(request):
    return render(request, 'PalletPricer/index.html')
