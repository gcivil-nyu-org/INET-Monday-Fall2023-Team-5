document.addEventListener('DOMContentLoaded', function() {
  window.showChoices = function(element) {
    const fieldName = element.getAttribute('data-field');
    var choices = formChoices[fieldName];

    // Check if a dropdown is already open and remove it
    const existingDropdown = document.getElementById('customDropdown');
    if (existingDropdown) {
      existingDropdown.remove();
    }

    // Create a new div element to act as the dropdown
    const dropdown = document.createElement('div');
    dropdown.setAttribute('id', 'customDropdown');
    dropdown.className = 'dropdown-content';
    dropdown.style.display = 'block'; // Ensure the dropdown is visible

    // Populate the dropdown with divs as options
    choices.forEach(function(choice) {
      const optionDiv = document.createElement('div');
      optionDiv.textContent = choice[1];

      optionDiv.onclick = function() {
        element.textContent = choice[1]; // Replace the clicked text with the choice
        // Set the value of the hidden chosen form field
        const hiddenInputId = 'hidden' + fieldName.charAt(0).toUpperCase() + fieldName.slice(1);
         const hiddenInput = document.getElementById(hiddenInputId);
         if (hiddenInput) {
          //  hiddenInput.value to integer
           hiddenInput.value = parseInt(choice[0], 10);
         } else {
           console.error('Hidden input not found for id:', hiddenInputId);
         }
         dropdown.remove(); // Remove the dropdown
        };
      dropdown.appendChild(optionDiv);
    });

    // Position the dropdown next to the clicked element
    const elementRect = element.getBoundingClientRect();
    dropdown.style.left = `${elementRect.right + window.scrollX}px`; // Adjusted to right for better positioning
    dropdown.style.top = `${elementRect.top + window.scrollY}px`;

    // Append the dropdown to the body
    document.body.appendChild(dropdown);
  };

  // Function to handle clicking outside of dropdown to close it
  window.addEventListener('click', function(event) {
    if (!event.target.matches('.selectable')) {
      const dropdowns = document.getElementsByClassName('dropdown-content');
      for (let i = 0; i < dropdowns.length; i++) {
        dropdowns[i].style.display = 'none';
      }
    }
  }, true); // Use capture phase for this event
});
