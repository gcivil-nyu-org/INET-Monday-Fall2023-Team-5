$(document).ready(function () {
    // Make words draggable
    $('.draggable').draggable({
        helper: 'clone', // Create a clone of the draggable element
        revert: 'invalid', // The element will return to its position if not dropped in a valid droppable
        start: function(event, ui) {
            $(ui.helper).addClass('dragging'); // Add a class for styling if you want
        }
    });

    // Make the sentence container droppable
    $('#current-sentence').droppable({
        accept: '.draggable', // Accept elements with the .draggable class
        drop: function(event, ui) {
            // Append the text of the draggable item to the droppable container
            let wordText = $.trim($(ui.draggable).text());
            // Ensure it doesn't already exist
            if($('#current-sentence:contains("' + wordText + '")').length === 0) {
                $(this).append($('<span>').addClass('selected-word').text(wordText + ' '));
                $(ui.draggable).addClass('dragged'); // Add the 'dragged' class to the original word
            }
        }
    });

    // Clear All button functionality
    $('#clear-all').click(function() {
        // Clear the inner HTML of the sentence container
        $('#current-sentence').html('');
        
        // Remove the 'dragged' class from all elements that have been dragged
        $('.draggable.dragged').removeClass('dragged');
    });
});

