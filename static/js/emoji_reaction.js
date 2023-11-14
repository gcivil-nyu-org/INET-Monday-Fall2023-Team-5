// emoji_reactions.js

function recordEmoji(emoji) {
    const sessionId = document.getElementById("game-session-id").value; // Use a hidden input to store the session ID
    fetch(`/record_emoji_reaction/${sessionId}/`, { // Replace with the correct URL pattern
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'), // Add getCookie function to get the CSRF token
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ emoji: emoji })
    })
    .then(response => response.json())
    .then(data => {
        console.log(data); // Handle response
    });
}
function showEmojiReactions(emojiReactions) {
    const container = document.getElementById("emojiReactionsContainer");
    container.innerHTML = "";  // Clear previous reactions

    emojiReactions.forEach(reaction => {
        container.innerHTML += `<p>${reaction.emoji}: ${reaction.count}</p>`;
    });

    // Show the modal
    $('#emojiReactionModal').modal('show');
}

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

