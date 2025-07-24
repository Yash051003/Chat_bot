from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('inbox', views.inbox, name='inbox'),
    path('user/<int:user_id>/', views.chat_room, name='room'),
    path('conversation/<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('conversation/<int:conversation_id>/messages/', views.get_messages, name='get_messages'),
    path('check_new_messages/', views.check_new_messages, name='check_new_messages'),
    path('upload/', views.upload_image, name='upload_image'),
] 