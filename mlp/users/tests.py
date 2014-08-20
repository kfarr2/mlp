import os, sys, re, shutil, mock, tempfile
from model_mommy.mommy import make
from django.test import TestCase
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.unittest import skipIf
from .forms import LoginForm, UserForm, UserSearchForm
from .models import User


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

    i = User(first_name="Inactive", last_name="Bobby", email="InactiveBobby@pdx.edu", is_active=False)
    i.set_password("foobar")
    i.save()
    self.inactive = i


class UserViewsTest(TestCase):
    """
    Tests for user views
    """
    def setUp(self):
        super(UserViewsTest, self).setUp()
        create_users(self)
        self.client.login(email=self.admin.email, password="foobar")

    def test_home_view(self):
        self.client.logout()
        self.client.login(email=self.admin.email, password="foobar")
        response = self.client.get(reverse('users-home'))
        self.assertRedirects(response, reverse('users-list'))
        self.client.logout()
        
        self.client.login(email=self.user.email, password="foobar")
        response = self.client.get(reverse('users-home'))
        self.assertRedirects(response, reverse('users-workflow'))
        self.client.logout()
        self.client.login(email=self.admin.email, password="foobar")

    def test_list_view(self):
        response = self.client.get(reverse('users-list'))
        self.assertEqual(response.status_code, 200)

    def test_detail_view(self):
        response = self.client.get(reverse('users-detail', args=(self.admin.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_create_view(self):
        response = self.client.get(reverse('users-create'))
        self.assertEqual(response.status_code, 200)
        
        data = {
            "email":"foo@bar.com",
            "first_name": "foo",
            "last_name": "foo",
            "password":"foobar",
        }
        response = self.client.post(reverse('users-create'), data)
        self.assertRedirects(response, reverse('users-list'))

    def test_edit_view(self):
        data = {
            "email": self.admin.email,
            "first_name": "jimmy",
            "last_name": self.admin.last_name,
            "password": self.admin.password,
        }
        response = self.client.post(reverse('users-edit', args=(self.admin.pk,)), data)
        self.assertRedirects(response, reverse('users-list'))
        self.assertTrue(self.admin.first_name,"jimmy")

    def test_delete_view(self):
        pre_count = User.objects.count()
        response = self.client.get(reverse('users-delete', args=(self.user.pk,)))
        self.assertRedirects(response, reverse('users-list'))
        self.assertEqual(pre_count-1, User.objects.count())

        response = self.client.get(reverse('users-delete', args=(self.user.pk,)))
        self.assertEqual(response.status_code, 404)


class LoginFormTest(TestCase):
    """
    Test user forms
    """
    def setUp(self):
        super(LoginFormTest, self).setUp()
        create_users(self)

