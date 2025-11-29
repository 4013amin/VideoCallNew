# videocall/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # path('', views.video_chat_lobby, name='lobby'),
    path('lobby/', views.video_chat_lobby, name='lobby'),

    path('add_coins/', views.add_coins_view, name='add_coins'),

]