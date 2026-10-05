from django.test import TestCase
from django.urls import reverse


class SmokeTest(TestCase):
    def test_home_page_renders(self):
        response = self.client.get(reverse("main:show_main"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")
