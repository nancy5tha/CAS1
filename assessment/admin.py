from django.contrib import admin
from .models import Profile, AcademicYear, ExamTerm, Student, Subject, Assessment

admin.site.register(Profile)
admin.site.register(AcademicYear)
admin.site.register(ExamTerm)
admin.site.register(Student)
admin.site.register(Subject)
admin.site.register(Assessment)
