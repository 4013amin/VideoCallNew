from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from users.models import Profile
from users.models import Profile



@login_required
def video_chat_lobby(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'videocall/lobby.html', {'coins': profile.coins})


@login_required
@require_POST
def add_coins_view(request):
    profile = request.user.profile
    profile.coins += 5  
    profile.save()
    return redirect('lobby')  