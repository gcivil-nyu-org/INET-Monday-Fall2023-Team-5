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
        accept: '.draggable',
        drop: function(event, ui) {
            let wordText = $.trim($(ui.draggable).text());
            if ($('#current-sentence:contains("' + wordText + '")').length === 0) {
                var newWord = $('<span>').addClass('selected-word draggable').text(wordText + ' ').draggable({
                    helper: 'clone',
                    revert: 'invalid',
                    start: function(event, ui) {
                        $(ui.helper).addClass('dragging');
                    }
                });
                $(this).append(newWord);
    
                // Remove the original element if it's a clone
                if (ui.helper.is('.ui-draggable-helper')) {
                    $(ui.draggable).remove();
                }
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

    // Setup for allowing words to be dragged back to the tag-container
    $('#tag-container').droppable({
        accept: '.selected-word',
        drop: function(event, ui) {
            // Remove the clone (the dragged element)
            $(ui.draggable).remove();
        }
    });
        $('#answer-form').submit(function(event) {
        var selectedWords = [];
        $('#current-sentence .selected-word').each(function() {
            selectedWords.push($(this).text().trim());
        });

        var answer = selectedWords.join(' ');
        $('#hidden-answer-field').val(answer);
    });
});

