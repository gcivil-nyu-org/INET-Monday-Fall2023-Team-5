$(document).ready(function () {
    // Function to hide a draggable word (instead of removing)
    function hideDraggable(element) {
        element.css('visibility', 'hidden'); // Hide the element
    }

    // Function to show a draggable word (instead of creating new)
    function showDraggable(wordText) {
        $('.draggable').filter(function() {
            return $.trim($(this).text()) === wordText;
        }).css('visibility', 'visible'); // Show the element
    }

    // Function to add word to the sentence
    function addToSentence(element) {
        let wordText = $.trim(element.text());

        // Create a new word element and append it to the sentence
        var newWord = $('<span>').addClass('selected-word draggable').text(wordText + ' ').click(function() {
            removeFromSentence($(this));
        });

        $('#current-sentence').append(newWord);
        hideDraggable(element);
    }


    // Function to remove word from the sentence
    function removeFromSentence(element) {
        let wordText = $.trim(element.text());
        showDraggable(wordText);
        element.remove();
    }

    // Make words draggable and clickable
    // $('.draggable').each(function() {
    //     $(this).draggable({
    //         helper: 'clone',
    //         revert: 'invalid'
    //     }).click(function() {
    //         addToSentence($(this));
    //     });
    // });

    $('.draggable').draggable({
        helper: 'clone',
        revert: 'invalid'
    });

    // Attach click event to draggable elements
    $('.draggable').off('click').on('click', function() {
        addToSentence($(this));
    });

    // Make the sentence container sortable and droppable
    $('#current-sentence').sortable({
        items: '.selected-word',
        placeholder: 'sortable-placeholder'
    }).droppable({
        accept: '.draggable',
        drop: function(event, ui) {
            addToSentence(ui.helper);
        }
    });

    // Clear All button functionality
    $('#clear-all').click(function() {
        $('#current-sentence').empty();
        $('.draggable').css('visibility', 'visible'); // Show all hidden elements
    });

    // Setup for allowing words to be dragged back to the tag-container
    $('#tag-container').droppable({
        accept: '.selected-word',
        drop: function(event, ui) {
            removeFromSentence(ui.draggable);
        }
    });

    // Form submission logic
    $('#answer-form').submit(function(event) {
        var selectedWords = [];
        $('#current-sentence .selected-word').each(function() {
            selectedWords.push($(this).text().trim());
        });

        var answer = selectedWords.join(' ');
        $('#hidden-answer-field').val(answer);
    });
});
