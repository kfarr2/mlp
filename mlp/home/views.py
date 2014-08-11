import os
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import login as django_login, logout as django_logout, get_user_model
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.http import is_safe_url
from mlp.users.forms import LoginForm
from mlp.files.models import File

def home(request):
    """
    Default home view
    """
    files = File.objects.order_by('-uploaded_on')

    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse("users-home"))

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
        "files": files,
        "form": form,
    })
