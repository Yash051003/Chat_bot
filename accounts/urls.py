from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('profile/<str:username>/', views.profile, name='view_profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('update-location/', views.update_location, name='update_location'),
] 