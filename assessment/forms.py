from django import forms
from .models import Assessment

class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = ["student", "subject", "term",
                  "project", "classwork", "viva", "mcqs", "homework"]
