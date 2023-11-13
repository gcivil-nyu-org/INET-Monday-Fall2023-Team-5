document.addEventListener('DOMContentLoaded', function () {
    var browseProfileLink = document.getElementById('browse-profile-link');
    if (browseProfileLink) {
        browseProfileLink.addEventListener('click', function(event) {
            if (this.getAttribute('data-active') === 'false') {
                event.preventDefault();
                alert('This page is not available for you now.');
            }
        });
    }

    var playgroundLink = document.getElementById('playground-link');
    if (playgroundLink) {
        playgroundLink.addEventListener('click', function(event) {
            if (this.getAttribute('data-active') === 'false') {
                event.preventDefault();
                alert('This page is not available for you now.');
            }
        });
    }
});
