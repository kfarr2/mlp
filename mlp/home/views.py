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
from mlp.users.models import User
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
        intro_text = "The Mobile Learning Project brings together faculty from various Portland State University departments and units (World Languages and Literatures, Applied Linguistics, and the Literacy, Language, & Technology Research Group) as well as other national and international collaborators and research networks. Our efforts focus on two areas: (1) the design and implementation of formative pedagogical interventions that involve mobile and other digital technologies to create language learning opportunities, and (2) video-based research on the digital interventions we create that utilize interdisciplinary approaches associated with learning sciences and second language development research."

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

@login_required
def admin(request):
    """
    Admin page for editing the intro paragraph
    """
    if not request.user.is_staff:
        return HttpResponseRedirect(reverse('users-home'))
    
    intro_text = IntroText.objects.last()
    
    if request.POST:
        form = IntroTextForm(request.POST, instance=intro_text)
        if form.is_valid():
            messages.success(request, "Intro Text Updated.")
            form.save()
            intro_text = IntroText.objects.last()
    else:
        form = IntroTextForm(instance=intro_text)

    try:
        intro_text = intro_text.text 
    except AttributeError as e:
        intro_text = "The Mobile Learning Project brings together faculty from various Portland State University departments and units (World Languages and Literatures, Applied Linguistics, and the Literacy, Language, & Technology Research Group) as well as other national and international collaborators and research networks. Our efforts focus on two areas: (1) the design and implementation of formative pedagogical interventions that involve mobile and other digital technologies to create language learning opportunities, and (2) video-based research on the digital interventions we create that utilize interdisciplinary approaches associated with learning sciences and second language development research."

    return render(request, 'home/admin.html', {
        "intro_text": intro_text,
        "form": form,
    })
