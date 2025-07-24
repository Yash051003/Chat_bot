import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from .models import Message, Conversation
from accounts.models import User # Make sure to import your User model

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Called when the websocket is handshaking as part of connection.
        """
        # Get the conversation ID from the URL.
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        
        # The user object is available in self.scope['user'] because of AuthMiddlewareStack.
        self.user = self.scope['user']

        # Ensure the user is authenticated and part of the conversation.
        if not self.user.is_authenticated:
            await self.close()
            return

        # Join room group.
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave room group.
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Receive a message from the WebSocket.
        This method saves the message to the database and then broadcasts it.
        """
        data = json.loads(text_data)
        message_content = data.get('message')
        image_url = data.get('image_url') # For handling image messages

        if not message_content and not image_url:
            return # Don't process empty messages

        # Save the message to the database.
        message = await self.save_message(message_content, image_url)

        # Render the message HTML to send to the group.
        html = await self.render_message_html(message)

        # Send message to room group.
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'html': html,
                'sender_id': self.user.id
            }
        )

    async def chat_message(self, event):
        """
        Receive message from room group and forward it to the client's WebSocket.
        """
        html = event['html']
        sender_id = event['sender_id']

        # Send HTML to WebSocket.
        await self.send(text_data=json.dumps({
            'type': 'chat.message',
            'html': html,
            'sender_id': sender_id
        }))

    @database_sync_to_async
    def save_message(self, content, image_url=None):
        """
        Saves a new message object to the database.
        This runs in a synchronous context.
        """
        conversation = get_object_or_404(Conversation, id=self.conversation_id)
        
        # Note: If handling direct image uploads, you would save the file here.
        # This implementation assumes the image URL is already available from an upload view.
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content,
            # If you have an image, you'd handle the ImageField here.
            # For now, this assumes content or a URL is passed.
        )
        return message
        
    @database_sync_to_async
    def render_message_html(self, message):
        """
        Renders the message.html template with the message context.
        """
        return render_to_string(
            'chat/message.html', 
            {'message': message, 'request': self.scope}
        )
