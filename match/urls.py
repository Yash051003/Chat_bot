from django.urls import path
from . import views

app_name = 'match'

urlpatterns = [
    path('', views.home, name='home'),
    path('browse/', views.index, name='browse'),
    path('like/<int:user_id>/', views.like_user, name='like_user'),
    path('pass/<int:user_id>/', views.pass_user, name='pass_user'),
    path('matches/', views.matches, name='matches'),
    path('favorites/', views.favorites, name='favorites'),
    path('favorite/<int:user_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('explore/', views.explore, name='explore'),
] 