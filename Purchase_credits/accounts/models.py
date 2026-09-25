from django.contrib.auth.models import AbstractUser
from django.db import models

ROLE_CHOICES = [
    ("student", "学生"),
    ("professor", "教授"),
]


class User(AbstractUser):
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default="student")
    display_name = models.CharField(max_length=64, blank=True)
    student_number = models.CharField(max_length=16, blank=True)
    department = models.CharField(max_length=64, blank=True)

    def __str__(self):
        return self.display_name or self.username

    @property
    def is_student(self):
        return self.role == "student"

    @property
    def is_professor(self):
        return self.role == "professor"
