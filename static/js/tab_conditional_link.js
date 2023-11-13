document.addEventListener('DOMContentLoaded', function () {
    var browseProfileLink = document.getElementById('browse-profile-link');
    if (browseProfileLink) {
        browseProfileLink.addEventListener('click', function(event) {
            if (this.getAttribute('data-active') === 'false') {
                alert('This page is not available for you now.');
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
                alert('This page is not available for you now.');
            } else {
                var href = this.getAttribute('data-href');
                if (href) {
                    window.location.href = href;
                }
            }
        });
    }
});
