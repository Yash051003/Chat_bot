// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add animation classes to elements
    const animateElements = document.querySelectorAll('.card, .profile-card');
    animateElements.forEach(element => {
        element.classList.add('animate-fade-in');
    });

    // Handle like/pass buttons
    const likeButtons = document.querySelectorAll('.btn-like');
    const passButtons = document.querySelectorAll('.btn-pass');

    likeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const userId = this.dataset.userId;
            handleLike(userId);
        });
    });

    passButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const userId = this.dataset.userId;
            handlePass(userId);
        });
    });

    // Handle match animation
    const matchElement = document.querySelector('.match-animation');
    if (matchElement) {
        matchElement.addEventListener('animationend', function() {
            this.classList.remove('match-animation');
        });
    }

    // Smooth scroll for navigation
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Profile image hover effect
    const profileImages = document.querySelectorAll('.profile-image');
    profileImages.forEach(image => {
        image.addEventListener('mouseover', function() {
            this.style.transform = 'scale(1.05)';
        });
        image.addEventListener('mouseout', function() {
            this.style.transform = 'scale(1)';
        });
    });
});

// Handle like action
function handleLike(userId) {
    const form = document.querySelector(`form[action*="/like/${userId}/"]`);
    if (form) {
        const button = form.querySelector('button');
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Liking...';
        
        fetch(form.action, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
            if (data.match) {
                showMatchAnimation();
            }
            window.location.reload();
        })
        .catch(error => {
            console.error('Error:', error);
            button.disabled = false;
            button.innerHTML = '<i class="bi bi-heart-fill"></i> Like';
        });
    }
}

// Handle pass action
function handlePass(userId) {
    const form = document.querySelector(`form[action*="/pass/${userId}/"]`);
    if (form) {
        const button = form.querySelector('button');
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Passing...';
        
        fetch(form.action, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
            window.location.reload();
        })
        .catch(error => {
            console.error('Error:', error);
            button.disabled = false;
            button.innerHTML = '<i class="bi bi-x-lg"></i> Pass';
        });
    }
}

// Show match animation
function showMatchAnimation() {
    const matchOverlay = document.createElement('div');
    matchOverlay.className = 'match-overlay';
    matchOverlay.innerHTML = `
        <div class="match-content">
            <h2>It's a Match!</h2>
            <p>You and your match have liked each other!</p>
            <button class="btn btn-primary" onclick="this.parentElement.parentElement.remove()">Continue</button>
        </div>
    `;
    document.body.appendChild(matchOverlay);
}

// Get CSRF token from cookies
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