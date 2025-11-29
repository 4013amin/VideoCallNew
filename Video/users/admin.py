from django.contrib import admin
from .models import Profile, Payment

# Register your models here.




@admin.action(description='افزودن ۱۰ سکه به کاربران انتخاب شده')
def add_10_coins(modeladmin, request, queryset):
    for profile in queryset:
        profile.coins += 10
        profile.save()

    modeladmin.message_user(request, "۱۰ سکه به کاربران انتخاب شده اضافه شد.")


class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'coins']
    actions = [add_10_coins]


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Payment)
