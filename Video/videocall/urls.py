# videocall/urls.py
from django.urls import path
from . import views

urlpatterns = [
<<<<<<< HEAD
    # path('', views.video_chat_lobby, name='lobby'),
    path('lobby/', views.video_chat_lobby, name='lobby'),

    path('add_coins/', views.add_coins_view, name='add_coins'),

=======
    # نام را از 'lobby' به 'video_chat_lobby' تغییر دهید تا با فایل‌های HTML هماهنگ شود
    path('lobby/', views.video_chat_lobby, name='video_chat_lobby'),
    path('add_coins/', views.add_coins_view, name='add_coins_view'),
>>>>>>> ebfedfa (some message)
]