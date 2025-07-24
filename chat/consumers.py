import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.template.loader import render_to_string
from .models import Message, Conversation
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope['user'].is_authenticated:
            await self.close()
            return

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'chat.message':
                message = text_data_json.get('message', '').strip()
                image_url = text_data_json.get('image_url')
                
                if message or image_url:
                    # Save message to database
                    saved_message = await self.save_message(message, image_url)
                    
                    # Send message to room group
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': saved_message
                        }
                    )
        except json.JSONDecodeError:
            print("Error decoding JSON")
        except Exception as e:
            print(f"Error in receive: {str(e)}")

    async def chat_message(self, event):
        try:
            message = event['message']
            
            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                'type': 'chat.message',
                'html': await self.render_message(message)
            }))
        except Exception as e:
            print(f"Error in chat_message: {str(e)}")

    @database_sync_to_async
    def save_message(self, content, image_url=None):
        try:
            conversation = Conversation.objects.get(id=self.room_name)
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                content=content,
                image=image_url
            )
            return {
                'id': message.id,
                'content': message.content,
                'image_url': message.image.url if message.image else None,
                'sender_id': self.user.id,
                'sender_username': self.user.username,
                'timestamp': message.created_at.isoformat()
            }
        except Exception as e:
            print(f"Error saving message: {str(e)}")
            raise

    @database_sync_to_async
    def render_message(self, message_data):
        try:
            message = {
                'id': message_data['id'],
                'content': message_data['content'],
                'image_url': message_data.get('image_url'),
                'sender': self.user if message_data['sender_id'] == self.user.id else User.objects.get(id=message_data['sender_id']),
                'timestamp': timezone.datetime.fromisoformat(message_data['timestamp'])
            }
            return render_to_string('chat/message.html', {
                'message': message,
                'request': {'user': self.user}
            })
        except Exception as e:
            print(f"Error rendering message: {str(e)}")
            raise 