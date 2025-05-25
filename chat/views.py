from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Max, F, OuterRef, Subquery
from accounts.models import User
from .models import Message, Conversation

# Create your views here.

@login_required
def inbox(request):
    # Get all conversations for the current user with their latest message
    latest_message = Message.objects.filter(
        conversation=OuterRef('pk')
    ).order_by('-created_at')
    
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        latest_message_content=Subquery(
            latest_message.values('content')[:1]
        ),
        latest_message_time=Subquery(
            latest_message.values('created_at')[:1]
        ),
        other_user_id=Subquery(
            User.objects.filter(
                conversations=OuterRef('pk')
            ).exclude(
                id=request.user.id
            ).values('id')[:1]
        ),
        other_user_name=Subquery(
            User.objects.filter(
                conversations=OuterRef('pk')
            ).exclude(
                id=request.user.id
            ).values('username')[:1]
        )
    ).order_by('-latest_message_time')

    return render(request, 'chat/inbox.html', {
        'conversations': conversations
    })

@login_required
def chat_room(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    # Get or create conversation between the two users
    conversation, created = Conversation.objects.get_or_create_conversation(request.user, other_user)
    messages = Message.objects.filter(conversation=conversation).order_by('created_at')
    
    return render(request, 'chat/chat_room.html', {
        'other_user': other_user,
        'messages': messages,
        'conversation': conversation
    })

@login_required
@require_POST
def send_message(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    content = request.POST.get('content', '').strip()
    image = request.FILES.get('image')
    
    if content or image:
        message = Message.objects.create(
            conversation=conversation,
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
def get_messages(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    last_message_id = request.GET.get('last_message_id')
    
    messages = Message.objects.filter(conversation=conversation)
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
