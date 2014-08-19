import os, sys, re, shutil, mock, tempfile
from model_mommy.mommy import make
from django.test import TestCase
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.unittest import skipIf
from mlp.users.models import User

def create_users(self):
    """
    Create some users
    """
    a = User(first_name="Admin", last_name="Joe", email="adminjoe@pdx.edu", is_staff=True)
    a.set_password("foobar")
    a.save()
    self.admin = a

    u = User(first_name="User", last_name="Mike", email="usermike@pdx.edu")
    u.set_password("foobar")
    u.save()
    self.user = u

class HomeTest(TestCase):
    """
    Test the home view
    """
    def setUp(self):
        create_users(self)

    def test_home_get_no_login(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_home_get(self):
        self.client.login(email=self.user.email, password="foobar")
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)
        self.client.logout()
    
    def test_home_invalid_post(self):
        data = {
            "email": "foo@bar.com",
            "password": "bad password",
        }
        response = self.client.post(reverse('home'), data)
        self.assertEqual(response.status_code, 200)
    
    def test_home_valid_post(self):
        data = {
            "email": self.admin.email,
            "password": "foobar",
        }
        response = self.client.post(reverse('home'), data)
        self.assertEqual(response.status_code, 302)
