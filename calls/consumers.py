import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'call_{self.room_name}'

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
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'call.offer':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'call_offer',
                    'offer': data['offer'],
                    'caller': self.scope['user'].username,
                }
            )
        elif message_type == 'call.answer':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'call_answer',
                    'answer': data['answer'],
                    'answerer': self.scope['user'].username,
                }
            )
        elif message_type == 'call.ice_candidate':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'ice_candidate',
                    'candidate': data['candidate'],
                    'sender': self.scope['user'].username,
                }
            )
        elif message_type == 'call.end':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'call_ended',
                    'sender': self.scope['user'].username,
                }
            )

    async def call_offer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call.offer',
            'offer': event['offer'],
            'caller': event['caller'],
        }))

    async def call_answer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call.answer',
            'answer': event['answer'],
            'answerer': event['answerer'],
        }))

    async def ice_candidate(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call.ice_candidate',
            'candidate': event['candidate'],
            'sender': event['sender'],
        }))

    async def call_ended(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call.end',
            'sender': event['sender'],
        })) 