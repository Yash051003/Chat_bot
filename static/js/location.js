// Function to get user's current location
function getCurrentLocation() {
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(
            // Success callback
            function(position) {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;
                
                // Send location to server
                updateUserLocation(latitude, longitude);
            },
            // Error callback
            function(error) {
                console.error("Error getting location:", error);
                showLocationError(error);
            },
            // Options
            {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0
            }
        );
    } else {
        showLocationError({ message: "Geolocation is not supported by your browser" });
    }
}

// Function to update user's location on server
function updateUserLocation(latitude, longitude) {
    fetch('/accounts/update-location/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            latitude: latitude,
            longitude: longitude
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Location updated successfully');
        } else {
            console.error('Error updating location:', data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Function to show location error to user
function showLocationError(error) {
    const errorMessages = {
        1: "Please allow location access to find matches near you.",
        2: "Unable to determine your location. Please check your device settings.",
        3: "Location request timed out. Please try again."
    };
    
    const message = errorMessages[error.code] || error.message || "Error getting your location";
    
    // Create and show error message
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-warning alert-dismissible fade show';
    alertDiv.innerHTML = `
        <i class="bi bi-exclamation-triangle"></i> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.querySelector('.container').insertBefore(alertDiv, document.querySelector('.container').firstChild);
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

// Start location tracking when page loads
document.addEventListener('DOMContentLoaded', function() {
    getCurrentLocation();
    
    // Update location every 5 minutes
    setInterval(getCurrentLocation, 5 * 60 * 1000);
}); 