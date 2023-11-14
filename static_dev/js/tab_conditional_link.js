document.addEventListener('DOMContentLoaded', function () {
    var browseProfileLink = document.getElementById('browse-profile-link');
    if (browseProfileLink) {
        browseProfileLink.addEventListener('click', function(event) {
            if (this.getAttribute('data-active') === 'false') {
                alert('Users engaged in an active game session cannot access the "Browse Profiles" page.');
            } else {
                var href = this.getAttribute('data-href');
                if (href) {
                    window.location.href = href;
                }
            }
        });
    }

    var playgroundLink = document.getElementById('playground-link');
    if (playgroundLink) {
        playgroundLink.addEventListener('click', function(event) {
            if (this.getAttribute('data-active') === 'false') {
                alert('Only users who have been successfully matched can access the "Playground" page.');
            } else {
                var href = this.getAttribute('data-href');
                if (href) {
                    window.location.href = href;
                }
            }
        });
    }
});
