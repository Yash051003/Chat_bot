from django.db import models
from django.conf import settings
from django.db.models import Q

class ConversationManager(models.Manager):
    def get_or_create_conversation(self, user1, user2):
        # Look for existing conversation between these users
        conversation = self.filter(participants=user1).filter(participants=user2).first()
        if conversation:
            return conversation, False
        
        # Create new conversation if none exists
        conversation = self.create()
        conversation.participants.add(user1, user2)
        return conversation, True

class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ConversationManager()

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation #{self.id}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', null=True)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    image = models.ImageField(upload_to='message_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message #{self.id} from {self.sender.username}"
