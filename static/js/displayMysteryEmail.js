function revealSpoiler(element) {
    var cover = element.querySelector('.spoiler-cover');
    cover.style.opacity = '0';
    cover.style.pointerEvents = 'none';
}