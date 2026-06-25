from django.db import models
from django.contrib.auth.models import User
class AcademicYear(models.Model):
    year = models.CharField(max_length=9)  # e.g. "2026-2027"

    def __str__(self):
        return self.year

class ExamTerm(models.Model):
    name = models.CharField(max_length=50)  # e.g. "Term 1", "Final"
    year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.year})"

class Student(models.Model):
    name = models.CharField(max_length=100)
    roll = models.CharField(max_length=2)
    grade = models.CharField(max_length=10)
    sec = models.CharField(max_length=2)

    def __str__(self):
        return f"{self.name} (Grade {self.grade}-{self.sec})"

class Subject(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Assessment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    term = models.ForeignKey(ExamTerm, on_delete=models.CASCADE)
    year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, default=1)


    project = models.IntegerField(default=0)
    classwork = models.IntegerField(default=0)
    viva = models.IntegerField(default=0)
    mcqs = models.IntegerField(default=0)
    homework = models.IntegerField(default=0)

    @property
    def total(self):
        return self.project + self.classwork + self.viva + self.mcqs + self.homework

    def __str__(self):
        return f"{self.student} - {self.subject} ({self.term})"

class Profile(models.Model):
    ROLE_CHOICES = [
        ("Admin", "Admin"),
        ("Teacher", "Teacher"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} ({self.role})"