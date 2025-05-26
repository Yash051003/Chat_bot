// Cache for storing location data
const locationCache = {
    data: null,
    timestamp: null,
    maxAge: 5 * 60 * 1000 // 5 minutes
};

// Throttle function with improved timing
function throttle(func, limit) {
    let lastRun;
    let timeout;
    
    return function(...args) {
        if (!lastRun) {
            func.apply(this, args);
            lastRun = Date.now();
        } else {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                if ((Date.now() - lastRun) >= limit) {
                    func.apply(this, args);
                    lastRun = Date.now();
                }
            }, limit - (Date.now() - lastRun));
        }
    }
}

// Show loading state
function showLoadingState() {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'locationLoadingState';
    loadingDiv.className = 'position-fixed top-0 start-50 translate-middle-x p-3';
    loadingDiv.style.zIndex = '1050';
    loadingDiv.innerHTML = `
        <div class="alert alert-info d-flex align-items-center" role="alert">
            <div class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div>
                Updating your location...
            </div>
        </div>
    `;
    document.body.appendChild(loadingDiv);
}

// Hide loading state
function hideLoadingState() {
    const loadingDiv = document.getElementById('locationLoadingState');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

// Function to get user's current location with improved error handling
function getCurrentLocation() {
    return new Promise((resolve, reject) => {
        // Check cache first
        if (locationCache.data && locationCache.timestamp && 
            (Date.now() - locationCache.timestamp) < locationCache.maxAge) {
            return resolve(locationCache.data);
        }

        // Show loading state
        showLoadingState();

        // Check if geolocation is available
        if (!("geolocation" in navigator)) {
            hideLoadingState();
            showFallbackInterface();
            reject(new Error("Geolocation is not supported by your browser"));
            return;
        }

        navigator.geolocation.getCurrentPosition(
            // Success callback
            (position) => {
                const locationData = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy
                };

                // Update cache
                locationCache.data = locationData;
                locationCache.timestamp = Date.now();

                hideLoadingState();
                resolve(locationData);
            },
            // Error callback
            (error) => {
                hideLoadingState();
                handleLocationError(error);
                reject(error);
            },
            // Options
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 5000
            }
        );
    });
}

// Function to update user's location on server with retry logic
async function updateUserLocation(latitude, longitude) {
    const maxRetries = 3;
    let retryCount = 0;

    while (retryCount < maxRetries) {
        try {
            const response = await fetch('/accounts/update-location/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ latitude, longitude })
            });

            const data = await response.json();

            if (data.success) {
                console.log('Location updated successfully');
                updateUI(latitude, longitude);
                return true;
            } else {
                throw new Error(data.error || 'Failed to update location');
            }
        } catch (error) {
            retryCount++;
            if (retryCount === maxRetries) {
                console.error('Failed to update location after', maxRetries, 'attempts:', error);
                showLocationError({
                    message: 'Unable to update your location. Please try again later.'
                });
                return false;
            }
            // Wait before retrying (exponential backoff)
            await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, retryCount)));
        }
    }
}

// Function to update UI elements
function updateUI(latitude, longitude) {
    // Update map if it exists
    if (typeof map !== 'undefined' && map) {
        map.setView([latitude, longitude], 13);
        if (marker) {
            marker.setLatLng([latitude, longitude]);
        } else {
            marker = L.marker([latitude, longitude]).addTo(map);
        }
    }

    // Refresh nearby users if on matching page
    if (window.location.pathname.includes('/match/')) {
        refreshNearbyUsers();
    }
}

// Show fallback interface when geolocation is denied
function showFallbackInterface() {
    const fallbackDiv = document.createElement('div');
    fallbackDiv.className = 'alert alert-warning alert-dismissible fade show';
    fallbackDiv.innerHTML = `
        <h5><i class="bi bi-geo-alt-fill"></i> Location Access Required</h5>
        <p>We need your location to show you nearby matches. You can:</p>
        <ol>
            <li>Enable location access in your browser settings</li>
            <li>Enter your location manually (coming soon)</li>
            <li>Continue with limited functionality</li>
        </ol>
        <button type="button" class="btn btn-primary btn-sm me-2" onclick="requestLocationPermission()">
            <i class="bi bi-geo-alt"></i> Enable Location
        </button>
        <button type="button" class="btn btn-outline-secondary btn-sm" onclick="continueWithoutLocation()">
            Continue Without Location
        </button>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(fallbackDiv, container.firstChild);
    }
}

// Handle location errors with specific messages
function handleLocationError(error) {
    const errorMessages = {
        1: {
            title: "Location Access Denied",
            message: "Please enable location access in your browser settings to see nearby matches.",
            action: showFallbackInterface
        },
        2: {
            title: "Location Unavailable",
            message: "Unable to determine your location. Please check your device settings.",
            action: null
        },
        3: {
            title: "Location Timeout",
            message: "Location request timed out. Please try again.",
            action: () => setTimeout(getCurrentLocation, 1000)
        }
    };

    const errorInfo = errorMessages[error.code] || {
        title: "Location Error",
        message: error.message || "An unknown error occurred while getting your location.",
        action: null
    };

    showLocationError({
        title: errorInfo.title,
        message: errorInfo.message
    });

    if (errorInfo.action) {
        errorInfo.action();
    }
}

// Enhanced error display
function showLocationError({ title, message }) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-warning alert-dismissible fade show';
    alertDiv.innerHTML = `
        <h5 class="alert-heading">${title || 'Location Error'}</h5>
        <p class="mb-0">${message}</p>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
    }
}

// Function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Function to refresh nearby users
function refreshNearbyUsers() {
    const container = document.querySelector('.row-cols-1');
    if (container) {
        fetch(window.location.pathname)
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newContent = doc.querySelector('.row-cols-1');
                if (newContent) {
                    container.innerHTML = newContent.innerHTML;
                }
            });
    }
}

// Initialize location tracking
document.addEventListener('DOMContentLoaded', function() {
    // Initial location check
    getCurrentLocation()
        .then(({ latitude, longitude }) => updateUserLocation(latitude, longitude))
        .catch(error => console.error('Initial location error:', error));
    
    // Throttled update on cursor movement (every 5 seconds)
    const throttledUpdate = throttle(() => {
        getCurrentLocation()
            .then(({ latitude, longitude }) => updateUserLocation(latitude, longitude))
            .catch(error => console.error('Location update error:', error));
    }, 5000);
    
    document.addEventListener('mousemove', throttledUpdate);
    
    // Regular background updates (every 5 minutes)
    setInterval(() => {
        getCurrentLocation()
            .then(({ latitude, longitude }) => updateUserLocation(latitude, longitude))
            .catch(error => console.error('Background update error:', error));
    }, 5 * 60 * 1000);
}); 