from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Max, F, OuterRef, Subquery, Count, Case, When, IntegerField
from accounts.models import User
from .models import Message, Conversation

# Create your views here.

@login_required
def inbox(request):
    # Get all conversations for the current user with their latest message
    latest_message = Message.objects.filter(
        conversation=OuterRef('pk')
    ).order_by('-created_at')
    
    # Get unread message count subquery
    unread_count = Message.objects.filter(
        conversation=OuterRef('pk'),
        sender__in=User.objects.exclude(id=request.user.id),
        is_read=False
    ).values('conversation').annotate(
        count=Count('id')
    ).values('count')
    
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
        ),
        unread_messages=Subquery(
            unread_count,
            output_field=IntegerField()
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
    
    # Mark all messages in this conversation as read
    Message.objects.filter(
        conversation=conversation,
        sender=other_user,
        is_read=False
    ).update(is_read=True)
    
    # Get messages but only select necessary fields
    messages = Message.objects.filter(conversation=conversation).order_by('created_at').values(
        'id', 'content', 'sender', 'created_at', 'image'
    )
    
    # Convert messages to a format suitable for the template
    formatted_messages = [{
        'id': msg['id'],
        'content': msg['content'],
        'sender_id': msg['sender'],
        'created_at': msg['created_at'],
        'image': msg['image']
    } for msg in messages]
    
    # Get the last message ID without displaying it
    last_message_id = messages.last()['id'] if messages else 0
    
    return render(request, 'chat/chat_room.html', {
        'other_user': other_user,
        'messages': formatted_messages,
        'conversation': conversation,
        'last_message_id': last_message_id,
        'debug': False  # Disable debug output
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
            image=image,
            is_read=False
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

@login_required
def check_new_messages(request):
    # Get the count of unread messages for the current user
    unread_count = Message.objects.filter(
        conversation__participants=request.user,
        sender__in=User.objects.exclude(id=request.user.id),
        is_read=False
    ).count()
    
    # Get the latest message ID the user has seen (can be stored in session)
    last_seen_id = request.session.get('last_seen_message_id', 0)
    
    # Check if there are any new messages since last check
    latest_message = Message.objects.filter(
        conversation__participants=request.user,
        sender__in=User.objects.exclude(id=request.user.id)
    ).order_by('-id').first()
    
    new_messages = False
    if latest_message and latest_message.id > last_seen_id:
        new_messages = True
        request.session['last_seen_message_id'] = latest_message.id
    
    return JsonResponse({
        'unread_count': unread_count,
        'new_messages': new_messages
    })
