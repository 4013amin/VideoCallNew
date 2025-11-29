# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('purchase/', views.purchase_coins_view, name='purchase'),
    path('verify/', views.verify_payment_view, name='verify_payment'),
    path('logout/', views.logout_view, name='logout'),
]