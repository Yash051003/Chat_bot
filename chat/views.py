import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import OuterRef, Subquery, Count, IntegerField
from django.core.cache import cache

from accounts.models import User
from .models import Message, Conversation

@login_required
@require_POST
def send_message(request, conversation_id):
    """
    Handles the creation of a new message via a POST request.
    This is typically used if you are not using WebSockets for sending.
    """
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    content = request.POST.get('content', '').strip()
    
    if content:
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content
        )
        return JsonResponse({'status': 'success', 'message': 'Message sent.'})
    
    return JsonResponse({'status': 'error', 'message': 'Message cannot be empty.'}, status=400)

@login_required
def get_messages(request, conversation_id):
    """
    Fetches new messages for a conversation, optionally after a certain message ID.
    """
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    last_message_id = request.GET.get('last_message_id')
    
    messages = Message.objects.filter(conversation=conversation)
    if last_message_id:
        messages = messages.filter(id__gt=last_message_id)
    
    messages = messages.order_by('created_at')
    
    # Manually serialize the message data into a list of dictionaries
    formatted_messages = [{
        'id': msg.id,
        'content': msg.content,
        'image_url': msg.image.url if msg.image else None,
        'sender': msg.sender.username,
        'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for msg in messages]

    return JsonResponse({'messages': formatted_messages})

@login_required
def check_new_messages(request):
    """
    Checks for and returns the count of unread messages for the current user.
    """
    unread_count = Message.objects.filter(
        conversation__participants=request.user,
        is_read=False
    ).exclude(
        sender=request.user
    ).count()
    
    return JsonResponse({'unread_count': unread_count})


@login_required
def inbox(request):
    """
    Displays the user's conversation list.
    The query is optimized to fetch all necessary data in one go.
    """
    latest_message = Message.objects.filter(conversation=OuterRef('pk')).order_by('-created_at')
    
    unread_count = Message.objects.filter(
        conversation=OuterRef('pk'),
        sender=OuterRef('other_user_id'),
        is_read=False
    ).values('conversation').annotate(count=Count('id')).values('count')

    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        # Annotate details about the other participant in the conversation
        other_user_id=Subquery(
            User.objects.filter(conversations=OuterRef('pk')).exclude(id=request.user.id).values('id')[:1]
        ),
        other_user_name=Subquery(
            User.objects.filter(conversations=OuterRef('pk')).exclude(id=request.user.id).values('username')[:1]
        ),
        # Annotate details of the last message
        latest_message_content=Subquery(latest_message.values('content')[:1]),
        latest_message_time=Subquery(latest_message.values('created_at')[:1]),
        # Annotate the count of unread messages
        unread_messages=Subquery(unread_count, output_field=IntegerField())
    ).filter(
        latest_message_time__isnull=False  # Only show conversations with messages
    ).order_by('-latest_message_time')

    context = {'conversations': conversations}
    return render(request, 'chat/inbox.html', context)


@login_required
def chat_room(request, user_id):
    """
    Displays the chat room and message history with another user.
    """
    other_user = get_object_or_404(User, id=user_id)
    
    # Assumes a custom manager method on Conversation model for clarity
    conversation, created = Conversation.objects.get_or_create_conversation(request.user, other_user)
    
    # Mark incoming messages as read
    Message.objects.filter(conversation=conversation, sender=other_user, is_read=False).update(is_read=True)
    
    # Fetch message history, optimized with select_related
    messages = Message.objects.filter(conversation=conversation).select_related('sender').order_by('created_at')
    
    context = {
        'other_user': other_user,
        'messages': messages,
        'conversation': conversation,
        'ws_protocol': 'wss' if request.is_secure() else 'ws'
    }
    return render(request, 'chat/room.html', context)


@login_required
@require_POST
def upload_image(request, conversation_id):
    """
    Handles image uploads within a specific conversation.
    Note: The original view was flawed; this version correctly associates the image with a conversation.
    """
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    image = request.FILES.get('image')

    if not image:
        return JsonResponse({'success': False, 'error': 'No image provided'}, status=400)
    
    message = Message.objects.create(
        sender=request.user,
        conversation=conversation,
        image=image
    )
    
    return JsonResponse({'success': True, 'image_url': message.image.url})

# Note: The 'send_message', 'get_messages', and 'check_new_messages' views become largely
# redundant when a full WebSocket implementation is in place, as the client-side
# JavaScript will handle sending and receiving messages in real-time.
# They are kept here to maintain existing functionality.

# --- New Video/Audio Call Signaling Views ---

@login_required
@require_POST
def initiate_call(request):
    """
    View to signal the start of a call.
    It publishes an 'call.initiated' event to a Redis channel for the recipient.
    """
    try:
        data = json.loads(request.body)
        recipient_id = data.get('recipient_id')
        conversation_id = data.get('conversation_id')
        
        if not recipient_id or not conversation_id:
            return JsonResponse({'status': 'error', 'message': 'Missing recipient or conversation ID'}, status=400)
        
        # The channel name is specific to the recipient
        channel_name = f"user_{recipient_id}"
        
        # Publish an event to the recipient's channel via Redis
        cache.set(f'call_{conversation_id}', json.dumps({
            'caller_id': request.user.id,
            'caller_name': request.user.username,
        }), timeout=60) # Call offer expires in 60 seconds

        redis_conn = cache.client.get_client()
        redis_conn.publish(channel_name, json.dumps({
            'type': 'call.initiated',
            'conversation_id': conversation_id,
            'caller_name': request.user.username
        }))

        return JsonResponse({'status': 'ok', 'message': 'Call initiated'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)


@login_required
@require_POST
def webrtc_signal(request):
    """
    Handles relaying WebRTC signaling messages (SDP offers/answers, ICE candidates)
    between the two peers via Redis.
    """
    try:
        data = json.loads(request.body)
        recipient_id = data.get('recipient_id')
        signal_type = data.get('type') # e.g., 'offer', 'answer', 'candidate'
        
        if not all([recipient_id, signal_type]):
            return JsonResponse({'status': 'error', 'message': 'Missing recipient or signal type'}, status=400)

        # The channel name is specific to the recipient
        channel_name = f"user_{recipient_id}"
        
        # Add sender information to the payload before relaying
        data['sender_id'] = request.user.id

        redis_conn = cache.client.get_client()
        redis_conn.publish(channel_name, json.dumps(data))
        
        return JsonResponse({'status': 'ok', 'message': 'Signal relayed'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)