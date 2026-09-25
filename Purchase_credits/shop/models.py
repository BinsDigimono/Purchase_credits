from django.conf import settings
from django.db import models
from django.urls import reverse


class Subject(models.Model):
    code = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=128)
    professor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    department = models.CharField(max_length=64, blank=True)
    term = models.CharField(max_length=32, blank=True)
    credits = models.PositiveSmallIntegerField(default=2)
    price = models.PositiveIntegerField()
    stock = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} {self.name}"

    def get_absolute_url(self):
        return reverse("shop:subject_detail", args=[self.pk])

    @property
    def is_sold_out(self):
        return self.stock <= 0


class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["subject__code"]
        unique_together = ["user", "subject"]

    def __str__(self):
        return f"{self.user} / {self.subject}"


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_price = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.pk} {self.user}"

    def get_absolute_url(self):
        return reverse("shop:order_detail", args=[self.pk])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT)
    # 買った時の値をコピーしておく
    subject_code = models.CharField(max_length=16)
    subject_name = models.CharField(max_length=128)
    professor_name = models.CharField(max_length=128)
    price = models.PositiveIntegerField()

    def __str__(self):
        return self.subject_name
