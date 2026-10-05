from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.html import strip_tags

from main.models import Note


class NoteForm(ModelForm):
    class Meta:
        model = Note
        fields = ["title", "content"]

    def clean_title(self):
        title = strip_tags(self.cleaned_data["title"]).strip()
        if not title:
            raise ValidationError("Judul tidak boleh hanya berisi tag HTML.")
        return title

    def clean_content(self):
        return strip_tags(self.cleaned_data["content"]).strip()
