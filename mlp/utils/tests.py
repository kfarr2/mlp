from unittest.mock import patch
from django.conf import settings
from django.db import transaction, IntegrityError
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.test import TestCase, TransactionTestCase

from mlp.users.models import User

# Tests all those non-app-specific things
class UtilsTest(TransactionTestCase):

    def setUp(self):
        super(UtilsTest, self).setUp()

    @transaction.atomic
    def test_atomic_requests(self):
        """
        Takes a count of current user objects, adds a valid user through a request, but forces an
        error causing the atomic transaction to fail and no changes to the database.
        """
        count = User.objects.count()
        data = {
            "email": "bar@bar.gov",
            "first_name": "Winning",
            "last_name": "Stuff",
            "password": "derp",
        }
        with patch('django.http.HttpResponseRedirect', side_effect=IntegrityError("foo")):
            try:
                response = self.client.post(reverse('users-create'), data)
                self.assertEqual(response.status_code, 302)
            except:
                pass

        users = User.objects.filter(email="bar@bar.gov").count()
        self.assertEqual(0, users)
        self.assertEqual(count, User.objects.count())
