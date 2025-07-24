from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, F
from django.db.models.functions import ACos, Cos, Sin, Radians
from django.core.paginator import Paginator
from math import radians, cos, sin, asin, sqrt
from accounts.models import User
from .models import Like, Match, UserProfile, Favorite
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
    current_user = request.user
    return render(request, 'match/home.html', {'current_user': current_user})

@login_required
def index(request):
    current_user = request.user
    # Get users that the current user has liked
    liked_users = Like.objects.filter(from_user=current_user).values_list('to_user', flat=True)
    # Get users that have liked the current user
    liked_by_users = Like.objects.filter(to_user=current_user).values_list('from_user', flat=True)
    
    # Get potential matches excluding users that have been liked or have liked the current user
    potential_matches = User.objects.exclude(
        Q(id=current_user.id) | 
        Q(id__in=liked_users) |
        Q(id__in=liked_by_users)
    ).order_by('-date_joined')
    
    paginator = Paginator(potential_matches, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'potential_matches': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'match/index.html', context)

@login_required
def like_user(request, user_id):
    liked_user = get_object_or_404(User, id=user_id)
    # Create a like
    Like.objects.create(from_user=request.user, to_user=liked_user)
    
    # Check if it's a match
    if Like.objects.filter(from_user=liked_user, to_user=request.user).exists():
        # Create a match
        match = Match.objects.create()
        match.users.add(request.user, liked_user)
        messages.success(request, f'It\'s a match with {liked_user.username}!')
    
    return redirect('match:browse')

@login_required
def pass_user(request, user_id):
    # For now, just redirect back to browse
    # In the future, you might want to store this information to avoid showing the same user again
    return redirect('match:browse')

@login_required
def matches(request):
    current_user = request.user
    # Get all matches for the current user
    matches = Match.objects.filter(users=current_user).prefetch_related('users')
    
    context = {
        'matches': matches,
    }
    return render(request, 'match/matches.html', context)

def landing_page(request):
    """
    Checks if a user is logged in.
    - If logged in, redirects to the browse page.
    - If not logged in, shows the public landing page.
    """
    if request.user.is_authenticated:
        return redirect('match:browse') # Redirects logged-in users
    
    return render(request, 'match/landing.html') # Shows landing page for visitors

@login_required
def browse(request):
    current_user = request.user
    MAX_RADIUS_KM = 50  # Maximum radius to show users
    
    # Get the current user's location
    user_lat = current_user.latitude
    user_lon = current_user.longitude
    
    if not user_lat or not user_lon:
        # If user location is not available, return users without distance sorting
        potential_matches = User.objects.exclude(id=current_user.id)
    else:
        # Calculate distance using the Haversine formula
        potential_matches = User.objects.exclude(id=current_user.id).annotate(
            distance=6371 * ACos(
                Sin(Radians(user_lat)) * Sin(Radians(F('latitude'))) +
                Cos(Radians(user_lat)) * Cos(Radians(F('latitude'))) *
                Cos(Radians(F('longitude')) - Radians(user_lon))
            )
        ).exclude(
            Q(latitude__isnull=True) | Q(longitude__isnull=True)
        ).filter(
            # Filter users within the maximum radius
            distance__lte=MAX_RADIUS_KM
        ).order_by('distance')  # Sort by nearest first

    paginator = Paginator(potential_matches, 9)  # Show 9 profiles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'match/explore.html', {
        'potential_matches': page_obj,
        'page_obj': page_obj,
    })

@login_required
def favorites(request):
    # Get users that the current user has favorited
    favorite_users = User.objects.filter(favorited_by__user=request.user)
    return render(request, 'match/favorites.html', {
        'favorite_users': favorite_users
    })

@login_required
def toggle_favorite(request, user_id):
    user_to_favorite = get_object_or_404(User, id=user_id)
    
    # Don't allow users to favorite themselves
    if user_to_favorite == request.user:
        messages.error(request, "You cannot favorite yourself.")
        return redirect('match:browse')
    
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        favorited_user=user_to_favorite
    )
    
    if not created:
        # If it already existed, remove it (unfavorite)
        favorite.delete()
        messages.success(request, f'Removed {user_to_favorite.username} from favorites')
    else:
        messages.success(request, f'Added {user_to_favorite.username} to favorites')
    
    # Redirect back to the previous page
    return redirect(request.META.get('HTTP_REFERER', 'match:browse'))

@login_required
def explore(request):
    current_user = request.user
    
    # Get the current user's location
    user_lat = current_user.latitude
    user_lon = current_user.longitude
    
    if not user_lat or not user_lon:
        # If user location is not available, return users without distance sorting
        explore_users = User.objects.exclude(id=current_user.id).order_by('?')
    else:
        # Calculate distance using the Haversine formula
        explore_users = User.objects.exclude(id=current_user.id).annotate(
            distance=6371 * ACos(
                Sin(Radians(user_lat)) * Sin(Radians(F('latitude'))) +
                Cos(Radians(user_lat)) * Cos(Radians(F('latitude'))) *
                Cos(Radians(F('longitude')) - Radians(user_lon))
            )
        ).exclude(
            Q(latitude__isnull=True) | Q(longitude__isnull=True)
        ).order_by('?')  # Random ordering for explore
    
    return render(request, 'match/explore.html', {
        'explore_users': explore_users
    })
