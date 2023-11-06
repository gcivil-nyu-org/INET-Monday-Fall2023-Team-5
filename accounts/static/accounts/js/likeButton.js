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

const csrftoken = getCookie('csrftoken');

document.querySelector('.like-button').addEventListener('click', function() {
    const userId = this.getAttribute('data-user-id');
    fetch(`/accounts/like-profile/${userId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({
            'action': 'like'
        })
    })
    .then(response => response.json())
    .then(data => {
        if(data.success) {
            document.getElementById('likes-count').innerText = data.likes_remaining;
            this.classList.add('active');
        } else {
            alert(data.error);
        }
    });
});