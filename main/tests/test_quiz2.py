from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from main.forms import NoteForm
from main.models import Note

PASSWORD = "Rahasia#123"


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password=PASSWORD)

    def test_register_page_renders_form(self):
        response = self.client.get(reverse("main:register"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_register_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse("main:register"),
            {"username": "bob", "password1": PASSWORD, "password2": PASSWORD},
        )
        self.assertRedirects(response, reverse("main:login"))
        self.assertTrue(User.objects.filter(username="bob").exists())

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse("main:register"),
            {"username": "bob", "password1": PASSWORD, "password2": "Beda#456"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="bob").exists())

    def test_login_success_sets_session_and_cookie(self):
        response = self.client.post(
            reverse("main:login"), {"username": "alice", "password": PASSWORD}
        )
        self.assertRedirects(response, reverse("main:show_notes"))
        self.assertIn("_auth_user_id", self.client.session)
        self.assertIn("last_login", response.cookies)

    def test_login_wrong_password_stays_on_page(self):
        response = self.client.post(
            reverse("main:login"), {"username": "alice", "password": "salah"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("last_login", response.cookies)

    def test_logout_clears_session_and_cookie(self):
        self.client.login(username="alice", password=PASSWORD)
        response = self.client.get(reverse("main:logout"))
        self.assertRedirects(response, reverse("main:login"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.cookies["last_login"].value, "")


class NotesPageTests(TestCase):
    def setUp(self):
        User.objects.create_user(username="alice", password=PASSWORD)

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(reverse("main:show_notes"))
        self.assertRedirects(response, "/login/?next=/notes/")

    def test_logged_in_user_sees_username_and_last_login(self):
        self.client.login(username="alice", password=PASSWORD)
        self.client.cookies["last_login"] = "2026-10-07 10:00:00"
        response = self.client.get(reverse("main:show_notes"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "notes.html")
        self.assertContains(response, "alice")
        self.assertContains(response, "2026-10-07 10:00:00")


class NoteFormTests(TestCase):
    def test_form_strips_tags(self):
        form = NoteForm(data={"title": "<b>Tebal</b>", "content": "<i>miring</i>"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["title"], "Tebal")
        self.assertEqual(form.cleaned_data["content"], "miring")

    def test_form_rejects_title_that_is_only_tags(self):
        form = NoteForm(data={"title": "<img src=x onerror=alert(1)>"})
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_form_rejects_long_title(self):
        form = NoteForm(data={"title": "a" * 101})
        self.assertFalse(form.is_valid())


class NotesAjaxTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password=PASSWORD)
        self.bob = User.objects.create_user(username="bob", password=PASSWORD)
        Note.objects.create(user=self.alice, title="Catatan Alice", content="Isi A")
        Note.objects.create(user=self.bob, title="Catatan Bob", content="Isi B")
        self.client.login(username="alice", password=PASSWORD)

    def test_json_returns_only_own_notes(self):
        response = self.client.get(reverse("main:notes_json"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        titles = [note["fields"]["title"] for note in response.json()]
        self.assertEqual(titles, ["Catatan Alice"])

    def test_json_anonymous_gets_401_json(self):
        self.client.logout()
        response = self.client.get(reverse("main:notes_json"))
        self.assertEqual(response.status_code, 401)
        self.assertIn("message", response.json())

    def test_create_ajax_success(self):
        response = self.client.post(
            reverse("main:create_note_ajax"), {"title": "Baru", "content": "Isi baru"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("pk", response.json())
        self.assertTrue(Note.objects.filter(user=self.alice, title="Baru").exists())

    def test_create_ajax_strips_html_tags(self):
        response = self.client.post(
            reverse("main:create_note_ajax"),
            {"title": "<b>Tebal</b>", "content": "<script>alert(1)</script>Aman"},
        )
        self.assertEqual(response.status_code, 201)
        note = Note.objects.get(title="Tebal")
        self.assertNotIn("<script>", note.content)

    def test_create_ajax_rejects_empty_title(self):
        response = self.client.post(reverse("main:create_note_ajax"), {"title": "   "})
        self.assertEqual(response.status_code, 400)
        self.assertIn("title", response.json()["errors"])
        self.assertEqual(Note.objects.count(), 2)

    def test_create_ajax_rejects_get(self):
        response = self.client.get(reverse("main:create_note_ajax"))
        self.assertEqual(response.status_code, 405)

    def test_create_ajax_anonymous_gets_401(self):
        self.client.logout()
        response = self.client.post(reverse("main:create_note_ajax"), {"title": "X"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Note.objects.count(), 2)

    def test_create_ajax_enforces_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(username="alice", password=PASSWORD)
        response = csrf_client.post(reverse("main:create_note_ajax"), {"title": "X"})
        self.assertEqual(response.status_code, 403)


class NotesHtmxTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password=PASSWORD)
        self.bob = User.objects.create_user(username="bob", password=PASSWORD)
        self.bob_note = Note.objects.create(user=self.bob, title="Catatan Bob")
        self.client.login(username="alice", password=PASSWORD)

    def test_htmx_page_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("main:show_notes_htmx"))
        self.assertEqual(response.status_code, 302)

    def test_htmx_create_returns_partial_with_new_note(self):
        response = self.client.post(
            reverse("main:create_note_htmx"), {"title": "HTMX", "content": "Isi"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "_notes_section.html")
        self.assertNotContains(response, "<html")
        self.assertContains(response, "HTMX")
        self.assertNotContains(response, "Catatan Bob")

    def test_htmx_create_invalid_keeps_errors_in_partial(self):
        response = self.client.post(reverse("main:create_note_htmx"), {"title": ""})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertFalse(Note.objects.filter(user=self.alice).exists())

    def test_htmx_delete_own_note(self):
        note = Note.objects.create(user=self.alice, title="Hapus aku")
        response = self.client.delete(reverse("main:delete_note_htmx", args=[note.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")
        self.assertFalse(Note.objects.filter(pk=note.id).exists())

    def test_htmx_cannot_delete_other_users_note(self):
        url = reverse("main:delete_note_htmx", args=[self.bob_note.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Note.objects.filter(pk=self.bob_note.id).exists())

    def test_htmx_delete_rejects_post(self):
        url = reverse("main:delete_note_htmx", args=[self.bob_note.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)
