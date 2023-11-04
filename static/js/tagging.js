$(document).ready(function () {
    $(".draggable").click(function() {
        let wordText = $(this).text();
        let currentSentence = $("#current-sentence").text();

        // Append the word to the sentence
        $("#current-sentence").text(currentSentence + " " + wordText);
    });
});
