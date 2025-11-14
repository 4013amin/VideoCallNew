# videocall/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from users.models import Profile


@login_required
def video_chat_lobby(request):
    # Pass coin count to the template
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        # Create profile if it somehow doesn't exist
        profile = Profile.objects.create(user=request.user)

    return render(request, 'videocall/lobby.html', {'coins': profile.coins})


@login_required
@require_POST
def add_coins_view(request):
    """A simple view to simulate purchasing coins."""
    profile = request.user.profile
    profile.coins += 5  # Add 5 coins per "purchase"
    profile.save()
    return redirect('lobby')  # Redirect back to the lobby