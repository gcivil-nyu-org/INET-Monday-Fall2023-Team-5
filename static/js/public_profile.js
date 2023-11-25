document.addEventListener('DOMContentLoaded', function() {
  // Function to show the dropdown for choices
  window.showChoices = function(element) {
    // Get the field name and the choices for that field
    const fieldName = element.getAttribute('data-field');
    var choices = formChoices[fieldName];

    // Create a new select element
    const select = document.createElement('select');
    select.setAttribute('name', fieldName);

    // Populate the select element with options
    choices.forEach(function(choice) {
      const option = document.createElement('option');
      option.value = choice[0];
      option.textContent = choice[1];
      select.appendChild(option);
    });

    // Insert the select element temporarily to calculate the position
    document.body.appendChild(select);

    // Calculate the position relative to the clicked element
    const elementRect = element.getBoundingClientRect();
    const selectRect = select.getBoundingClientRect();

    // Position the select element
    select.style.position = 'absolute';
    select.style.left = `${elementRect.left + window.scrollX}px`;
    select.style.top = `${elementRect.bottom + window.scrollY}px`;

    // Move the select back into the clicked element, now properly positioned
    element.textContent = ''; // Clear the text content
    element.appendChild(select);

    // Handle selection of an option
    select.onchange = function() {
      element.textContent = this.options[this.selectedIndex].textContent;
      document.querySelector(`input[name="${fieldName}"]`).value = this.value;
      // Remove the select element from the document body if it's appended there
      if (select.parentNode === document.body) {
        document.body.removeChild(select);
      }
    };

    // Add a blur event listener to remove the select element when it loses focus
    select.addEventListener('blur', function() {
      // Remove the select element from the document body if it's appended there
      if (select.parentNode === document.body) {
        document.body.removeChild(select);
      }
      // Restore the original text if no option was selected
      if (!element.textContent.trim()) {
        element.textContent = `[${fieldName}]`;
      }
    });

    // Focus the select element to allow keyboard interaction
    select.focus();
  };

  // Attach the showChoices function to the clickable elements
  document.querySelectorAll('[data-field]').forEach(function(element) {
    element.onclick = function() { showChoices(this); };
  });
});