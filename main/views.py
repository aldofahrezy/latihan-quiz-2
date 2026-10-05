import datetime

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from main.forms import NoteForm
from main.models import Note


def show_main(request):
    return render(request, "home.html")


# ---------- Drill 1: autentikasi ----------
def register(request):
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Akun berhasil dibuat. Silakan login.")
        return redirect("main:login")
    return render(request, "register.html", {"form": form})


def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        response = redirect("main:show_notes")
        response.set_cookie(
            "last_login", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        return response
    return render(request, "login.html", {"form": form})


def logout_user(request):
    logout(request)
    response = redirect("main:login")
    response.delete_cookie("last_login")
    return response


# ---------- Drill 2: halaman yang dilindungi ----------
@login_required(login_url="/login/")
def show_notes(request):
    context = {
        "username": request.user.username,
        "last_login": request.COOKIES.get("last_login", "Belum tercatat"),
    }
    return render(request, "notes.html", context)


# ---------- Drill 3 dan 4: endpoint AJAX (JSON) ----------
def unauthenticated_response():
    return JsonResponse({"message": "Silakan login terlebih dahulu."}, status=401)


def notes_json(request):
    if not request.user.is_authenticated:
        return unauthenticated_response()
    notes = Note.objects.filter(user=request.user).order_by("-created_at")
    data = [
        {
            "pk": str(note.id),
            "fields": {
                "title": note.title,
                "content": note.content,
                "created_at": note.created_at.isoformat(),
            },
        }
        for note in notes
    ]
    return JsonResponse(data, safe=False)


@require_POST
def create_note_ajax(request):
    if not request.user.is_authenticated:
        return unauthenticated_response()
    form = NoteForm(request.POST)
    if form.is_valid():
        note = form.save(commit=False)
        note.user = request.user
        note.save()
        return JsonResponse(
            {"message": "Catatan berhasil ditambahkan.", "pk": str(note.id)}, status=201
        )
    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)


# ---------- Drill 6: versi HTMX ----------
def notes_section_context(request, form=None):
    notes = Note.objects.filter(user=request.user).order_by("-created_at")
    return {"notes": notes, "form": form or NoteForm()}


@login_required(login_url="/login/")
def show_notes_htmx(request):
    return render(request, "notes_htmx.html", notes_section_context(request))


@login_required(login_url="/login/")
@require_POST
def create_note_htmx(request):
    form = NoteForm(request.POST)
    if form.is_valid():
        note = form.save(commit=False)
        note.user = request.user
        note.save()
        form = None
    return render(request, "_notes_section.html", notes_section_context(request, form))


@login_required(login_url="/login/")
@require_http_methods(["DELETE"])
def delete_note_htmx(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    note.delete()
    return HttpResponse("")
