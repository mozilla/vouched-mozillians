from django.core.urlresolvers import reverse
from django.http import HttpResponseNotAllowed
from django.test import Client
from django.test.utils import override_script_prefix
from nose.tools import eq_, ok_

from mozillians.common.tests import TestCase, requires_login
from mozillians.users.tests import UserFactory


class DeleteTests(TestCase):
    @requires_login()
    def test_confirm_delete_anonymous(self):
        client = Client()
        client.get(reverse('phonebook:profile_confirm_delete'), follow=True)

    def test_confirm_delete_unvouched(self):
        user = UserFactory.create(vouched=False)
        with self.login(user) as client:
            response = client.get(reverse('phonebook:profile_confirm_delete'),
                                  follow=True)
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'phonebook/confirm_delete.html')

    def test_confirm_delete_vouched(self):
        user = UserFactory.create()
        with self.login(user) as client:
            response = client.get(reverse('phonebook:profile_confirm_delete'),
                                  follow=True)
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'phonebook/confirm_delete.html')

    def test_delete_get_method(self):
        user = UserFactory.create()

        with override_script_prefix('/en-US'):
            url = reverse('phonebook:profile_delete')

        with self.login(user) as client:
            response = client.get(url, follow=True)
        ok_(isinstance(response, HttpResponseNotAllowed))

    @requires_login()
    def test_delete_anonymous(self):
        client = Client()
        client.post(reverse('phonebook:profile_delete'), follow=True)
