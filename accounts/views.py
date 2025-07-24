from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
import json
from .forms import UserRegistrationForm, UserProfileForm, UserLoginForm
from .models import User
from match.models import Like, Match
from match.views import calculate_distance

def login_view(request):
    if request.user.is_authenticated:
        return redirect('match:browse')
        
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                next_url = request.GET.get('next', 'match:browse')
                return redirect(next_url)
    else:
        form = UserLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('accounts:register')


def register(request):
    # If the user is already logged in, send them to the browse page directly.
    if request.user.is_authenticated:
        return redirect('match:browse') 
    
    if request.method == 'POST':
        # ... your existing POST logic is perfect ...
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Dating App!')
            return redirect('match:browse')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request, username=None):
    if username:
        profile_user = get_object_or_404(User, username=username)
    else:
        profile_user = request.user
    
    matches = profile_user.matches.all()
    likes_received = Like.objects.filter(to_user=profile_user).count()
    likes_given = Like.objects.filter(from_user=profile_user).count()
    
    # Calculate distance if both users have location data
    distance = None
    if request.user != profile_user and request.user.latitude and request.user.longitude and profile_user.latitude and profile_user.longitude:
        distance = calculate_distance(
            float(request.user.latitude),
            float(request.user.longitude),
            float(profile_user.latitude),
            float(profile_user.longitude)
        )
    
    context = {
        'profile_user': profile_user,
        'matches': matches,
        'likes_received': likes_received,
        'likes_given': likes_given,
        'distance': distance,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})

@login_required
@require_POST
@csrf_exempt
def update_location(request):
    try:
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if latitude is None or longitude is None:
            return JsonResponse({'success': False, 'error': 'Missing latitude or longitude'})
        
        user = request.user
        user.latitude = latitude
        user.longitude = longitude
        user.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})