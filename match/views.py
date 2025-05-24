from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from math import radians, cos, sin, asin, sqrt
from accounts.models import User
from .models import Like, Match
from django.contrib.auth import get_user_model

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points using the Haversine formula
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

@login_required
def home(request):
    # Get users that match preferences and haven't been liked/passed
    liked_users = Like.objects.filter(from_user=request.user).values_list('to_user', flat=True)
    passed_users = request.user.passed_users.all()
    
    potential_matches = User.objects.exclude(
        Q(id=request.user.id) |  # Exclude self
        Q(id__in=liked_users) |  # Exclude already liked
        Q(id__in=passed_users)   # Exclude passed
    ).filter(
        gender=request.user.looking_for,  # Match gender preference
        looking_for=request.user.gender   # Their preference matches user's gender
    )
    
    if potential_matches.exists():
        current_user = potential_matches.first()
    else:
        current_user = None
        messages.info(request, 'No more potential matches! Check back later.')
    
    return render(request, 'match/home.html', {'current_user': current_user})

@login_required(login_url='/login/')
def index(request):
    # Get users that match the current user's preferences
    current_user = request.user
    potential_matches = User.objects.exclude(
        id=current_user.id
    ).exclude(
        id__in=current_user.likes_given.values_list('to_user', flat=True)
    ).exclude(
        id__in=current_user.likes_received.values_list('from_user', flat=True)
    ).filter(
        Q(gender=current_user.looking_for) |  # Match gender preference
        Q(looking_for=current_user.gender)    # Their preference matches user's gender
    )

    context = {
        'potential_matches': potential_matches,
    }
    return render(request, 'match/index.html', context)

@login_required(login_url='/login/')
def like_user(request, user_id):
    current_user = request.user
    liked_user = User.objects.get(id=user_id)
    
    # Create like
    Like.objects.create(from_user=current_user, to_user=liked_user)
    
    # Check if it's a match
    if Like.objects.filter(from_user=liked_user, to_user=current_user).exists():
        Match.objects.create(users=[current_user, liked_user])
        messages.success(request, f'It\'s a match with {liked_user.username}!')
    
    return redirect('index')

@login_required(login_url='/login/')
def pass_user(request, user_id):
    current_user = request.user
    passed_user = User.objects.get(id=user_id)
    
    # Create a record of the pass (optional)
    # You might want to store this to avoid showing the same user again
    
    return redirect('index')

@login_required(login_url='/login/')
def matches(request):
    user = request.user
    matches = user.matches.all()
    
    context = {
        'matches': matches,
    }
    return render(request, 'match/matches.html', context)

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('index')
    return render(request, 'match/landing.html')
