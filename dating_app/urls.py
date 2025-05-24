"""
URL configuration for dating_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from match.views import index, landing_page, matches
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Main pages
    path('', landing_page, name='landing'),
    path('browse/', index, name='index'),
    path('matches/', matches, name='matches'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Authentication
    path('accounts/', include('accounts.urls')),
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        redirect_authenticated_user=True,
        next_page='/browse/'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        template_name='accounts/logout.html',
        next_page='landing',
        http_method_names=['get', 'post']
    ), name='logout'),
    
    # App features
    path('match/', include('match.urls')),
    path('chat/', include('chat.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
