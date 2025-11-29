from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    coins = models.IntegerField(default=5)


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField(verbose_name="مبلغ به تومان")
    coins_amount = models.IntegerField(verbose_name="تعداد سکه درخواستی")
    authority = models.CharField(max_length=255, verbose_name="شناسه پرداخت")
    is_paid = models.BooleanField(default=False, verbose_name="پرداخت شده")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} Toman"
