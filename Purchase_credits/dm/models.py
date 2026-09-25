from django.conf import settings
from django.db import models
from django.urls import reverse


# 学生と教授の1対1のトーク
class Thread(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_threads"
    )
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="professor_threads"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        unique_together = ["student", "professor"]

    def __str__(self):
        return f"{self.student} - {self.professor}"

    def get_absolute_url(self):
        return reverse("dm:thread_detail", args=[self.pk])

    # user から見た相手
    def partner(self, user):
        return self.professor if user == self.student else self.student


class Message(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    is_ai = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender}: {self.body[:20]}"
