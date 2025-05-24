from django.db import models
from django.conf import settings

# Create your models here.

class Like(models.Model):
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes_given')
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes_received')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user} likes {self.to_user}"

class Match(models.Model):
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='matches')
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Match between {', '.join(str(user) for user in self.users.all())}"
