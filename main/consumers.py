# main/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.room_name = f"user_{self.user.id}"
        
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        recipient_id = data['recipient']
        content = data['content']
        
        try:
            recipient = User.objects.get(id=recipient_id)
            message = await Message.objects.acreate(
                sender=self.user,
                recipient=recipient,
                content=content
            )
            
            # Send to recipient
            await self.channel_layer.group_send(
                f"user_{recipient.id}",
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'sender': self.user.username,
                        'content': content,
                        'timestamp': message.timestamp.isoformat(),
                    }
                }
            )
            
            # Send back to sender
            await self.send(text_data=json.dumps({
                'status': 'sent',
                'message': {
                    'id': message.id,
                    'sender': self.user.username,
                    'content': content,
                    'timestamp': message.timestamp.isoformat(),
                }
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'status': 'error',
                'error': str(e)
            }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))