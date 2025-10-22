# videocall/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('lobby/', views.video_chat_lobby, name='video_chat_lobby'),
    path('room/<str:room_name>/', views.room_view, name='room'),
]