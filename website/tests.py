from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class WebsiteFlowsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner@example.com",
            email="owner@example.com",
            password="123456Teste!",
        )

    def test_modelo_route_works(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("modelo"))
        self.assertEqual(response.status_code, 200)
