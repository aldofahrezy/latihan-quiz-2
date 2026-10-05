const noteForm = document.getElementById("note-form");
const noteList = document.getElementById("note-list");
const formError = document.getElementById("form-error");

// Membaca nilai cookie (pola yang sama dengan Tutorial 04 dan 05)
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Mengubah karakter khusus HTML menjadi entity agar tampil sebagai teks
function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function loadNotes() {
  try {
    const response = await fetch("/notes/json/", {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error(`Status ${response.status}`);
    const notes = await response.json();

    if (notes.length === 0) {
      noteList.innerHTML = "<li>Belum ada catatan.</li>";
      return;
    }
    noteList.innerHTML = notes
      .map(
        (note) => `
        <li class="card">
          <h3>${escapeHtml(note.fields.title)}</h3>
          <p>${escapeHtml(note.fields.content)}</p>
        </li>`,
      )
      .join("");
  } catch (error) {
    console.error("Error loading notes:", error);
    noteList.innerHTML = "<li>Gagal memuat catatan. Silakan coba lagi.</li>";
  }
}

async function addNote(event) {
  event.preventDefault();
  formError.textContent = "";
  const submitButton = noteForm.querySelector('button[type="submit"]');
  submitButton.disabled = true;

  try {
    const response = await fetch("/notes/create-ajax/", {
      method: "POST",
      headers: { "X-CSRFToken": getCookie("csrftoken") },
      body: new FormData(noteForm),
    });
    const result = await response.json().catch(() => ({}));

    if (response.ok) {
      noteForm.reset();
      await loadNotes();
    } else {
      const errorMessages = result.errors
        ? Object.values(result.errors).flat().map((error) => error.message)
        : [result.message || `Terjadi kesalahan (status ${response.status}).`];
      formError.textContent = errorMessages.join(" ");
    }
  } catch (error) {
    console.error("Error adding note:", error);
    formError.textContent = "Tidak dapat terhubung ke server. Silakan coba lagi.";
  } finally {
    submitButton.disabled = false;
  }
}

noteForm.addEventListener("submit", addNote);
loadNotes();
