import os
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import login as django_login, logout as django_logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.http import is_safe_url
from mlp.users.forms import LoginForm
from .models import IntroText
from .forms import IntroTextForm

def home(request):
    """
    Default home view
    """
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse("users-home"))
    try:
        intro_text = IntroText.objects.last().text
    except AttributeError as e:
        intro_text = "Welcome to the Mobile Learning Project"

    if request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():
            django_login(request, form.cleaned_data['user'])
            safe_url = reverse("users-home")
            url = form.cleaned_data.get("next", safe_url)
            if is_safe_url(url, host=request.get_host()):
                return HttpResponseRedirect(url)
        
            return HttpResponseRedirect(safe_url)
    else:
        form = LoginForm(initial=request.GET)

    return render(request, 'home/home.html', {
        "form": form,
        "intro_text": intro_text,
    })

def admin(request):
    """
    Admin page for editing the intro paragraph
    """
    intro_text = IntroText.objects.last()
    if request.POST:
        form = IntroTextForm(request.POST, instance=intro_text)
        if form.is_valid():
            messages.success(request, "Intro Text Updated.")
            form.save()
            return HttpResponseRedirect(reverse('home-admin'))
    else:
        form = IntroTextForm(instance=intro_text)

    intro_text = intro_text.text or "Welcome to the Mobile Learning Project"


    return render(request, 'home/admin.html', {
        "intro_text": intro_text,
        "form": form,
    })
