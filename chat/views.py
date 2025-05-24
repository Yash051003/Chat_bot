from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from match.models import Match
from .models import Message

# Create your views here.

@login_required
def chat_room(request, match_id):
    match = get_object_or_404(Match, id=match_id, users=request.user)
    other_user = match.users.exclude(id=request.user.id).first()
    messages = Message.objects.filter(match=match).order_by('created_at')
    
    return render(request, 'chat/chat_room.html', {
        'match': match,
        'other_user': other_user,
        'messages': messages
    })

@login_required
@require_POST
def send_message(request, match_id):
    match = get_object_or_404(Match, id=match_id, users=request.user)
    content = request.POST.get('content', '').strip()
    image = request.FILES.get('image')
    
    if content or image:
        message = Message.objects.create(
            match=match,
            sender=request.user,
            content=content,
            image=image
        )
        return JsonResponse({
            'status': 'success',
            'message': {
                'content': message.content,
                'image_url': message.image.url if message.image else None,
                'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    return JsonResponse({'status': 'error', 'message': 'Message cannot be empty'})

@login_required
def get_messages(request, match_id):
    match = get_object_or_404(Match, id=match_id, users=request.user)
    last_message_id = request.GET.get('last_message_id')
    
    messages = Message.objects.filter(match=match)
    if last_message_id:
        messages = messages.filter(id__gt=last_message_id)
    
    messages = messages.order_by('created_at')
    
    return JsonResponse({
        'messages': [{
            'id': msg.id,
            'content': msg.content,
            'image_url': msg.image.url if msg.image else None,
            'sender': msg.sender.username,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for msg in messages]
    })
