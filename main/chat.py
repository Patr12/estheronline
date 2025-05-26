# main/chat.py
from django.db.models import Q
from .models import Message

def get_conversations(user):
    """Get all unique conversations for a user"""
    conversations = Message.objects.filter(
        Q(sender=user) | Q(recipient=user)
    ).order_by('-timestamp')
    
    participants = set()
    unique_conversations = []
    
    for msg in conversations:
        other_user = msg.recipient if msg.sender == user else msg.sender
        if other_user not in participants:
            participants.add(other_user)
            unique_conversations.append({
                'user': other_user,
                'last_message': msg.content,
                'timestamp': msg.timestamp,
                'unread': Message.objects.filter(
                    sender=other_user,
                    recipient=user,
                    is_read=False
                ).count()
            })
    
    return unique_conversations