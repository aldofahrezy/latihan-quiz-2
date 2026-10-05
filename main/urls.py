from django.urls import path

from main.views import (
    create_note_ajax,
    create_note_htmx,
    delete_note_htmx,
    login_user,
    logout_user,
    notes_json,
    register,
    show_main,
    show_notes,
    show_notes_htmx,
)

app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("register/", register, name="register"),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),
    path("notes/", show_notes, name="show_notes"),
    path("notes/json/", notes_json, name="notes_json"),
    path("notes/create-ajax/", create_note_ajax, name="create_note_ajax"),
    path("notes/htmx/", show_notes_htmx, name="show_notes_htmx"),
    path("notes/htmx/create/", create_note_htmx, name="create_note_htmx"),
    path("notes/htmx/<uuid:pk>/delete/", delete_note_htmx, name="delete_note_htmx"),
]
