document.addEventListener('DOMContentLoaded', function() {
    let likeButton = document.querySelector('.btn-like');
    let profileId = likeButton.getAttribute('data-profile-id');

    // Check if the event listener has already been added
    if (!likeButton.getAttribute('data-event-listener-added')) {
        likeButton.setAttribute('data-event-listener-added', 'true');
        
        likeButton.addEventListener('click', function() {
            if (this.classList.contains('liked')) {
                alert('You have already liked this person before.');
            } else {
                // this.classList.add('liked');
                // Assuming you're using Django's CSRF token setup
                fetch(`/accounts/like-profile/${profileId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: JSON.stringify({
                        'action': 'like'
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if(data.success) {
                        document.getElementById('likes-count').innerText = data.likes_remaining;
                        this.classList.add('liked');
                        console.log('Like class added:', this);
                    } else {
                        // this.classList.remove('liked'); // Revert the like button state if the action wasn't successful
                        alert(data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    this.classList.remove('liked'); // Revert the like button state if there was a network error
                });
            }
        });
    }
});

// Function to get CSRF token
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
