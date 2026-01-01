from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    coins = models.IntegerField(default=5)

    def __str__(self):
        return f"Profile of {self.user.username}"

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField(verbose_name="مبلغ به تومان")
    coins_amount = models.IntegerField(verbose_name="تعداد سکه درخواستی")
    authority = models.CharField(max_length=255, verbose_name="شناسه پرداخت")
    is_paid = models.BooleanField(default=False, verbose_name="پرداخت شده")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} Toman"



@receiver(post_save, sender=User, dispatch_uid="create_user_profile_unique_id")
def manage_user_profile(sender, instance, created, **kwargs):
    if created:
        # با استفاده از get_or_create خیالت راحت می‌شود که اگر وجود داشت، دوباره نمی‌سازد
        Profile.objects.get_or_create(user=instance)
    else:
        # اگر یوزر از قبل بود، فقط پروفایلش را ذخیره کن (اگر داشت)
        if hasattr(instance, 'profile'):
            instance.profile.save()