from django.urls import path
from . import views

urlpatterns = [
    path('match/<int:match_id>/', views.chat_room, name='chat_room'),
    path('match/<int:match_id>/send/', views.send_message, name='send_message'),
    path('match/<int:match_id>/messages/', views.get_messages, name='get_messages'),
] 