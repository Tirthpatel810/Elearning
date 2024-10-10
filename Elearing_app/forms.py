from django import forms
from .models import Course

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'description', 'price', 'discount', 'active', 'thumbnail', 'resources', 'course_length']
