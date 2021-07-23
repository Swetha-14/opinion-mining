from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxLengthValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from profanity.validators import validate_is_profane

class User(AbstractUser):
    followers = models.ManyToManyField('self',symmetrical = False, related_name='following', blank=True)


class Post(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='images/', blank=True, null = True)
    likes = models.ManyToManyField('User', related_name="liked_posts", blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def serialize(self):
        return {
            "id": self.id,
            "user": self.user.username,
            "content": self.content,
            "likes": self.likes,
            "timestamp": self.timestamp.strftime("%b %-d %Y, %-I:%M %p")
        }


class Comment(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="commented_user")
    post = models.ForeignKey("Post", on_delete=models.CASCADE, related_name="comments")
    comment = models.TextField(max_length=500, validators=[validate_is_profane])