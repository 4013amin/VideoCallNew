from django.shortcuts import render
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def video_chat_lobby(request):
    return render(request, 'videocall/lobby.html')

@login_required
def room_view(request, room_name):
    return render(request, 'videocall/room.html', {
        'room_name': room_name,
        'username': request.user.username,
    })