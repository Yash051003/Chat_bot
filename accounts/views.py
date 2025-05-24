from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from .forms import UserRegistrationForm, UserProfileForm
from .models import User
from match.models import Like, Match

def register(request):
    if request.user.is_authenticated:
        return redirect('/browse/')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Dating App!')
            return redirect('/browse/')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required(login_url='/login/')
def profile(request):
    user = request.user
    matches = user.matches.all()
    likes_received = Like.objects.filter(to_user=user).count()
    likes_given = Like.objects.filter(from_user=user).count()
    
    context = {
        'user': user,
        'matches': matches,
        'likes_received': likes_received,
        'likes_given': likes_given,
    }
    return render(request, 'accounts/profile.html', context)

@login_required(login_url='/login/')
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('/accounts/profile/')
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
