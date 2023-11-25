document.addEventListener('DOMContentLoaded', function() {
  // Function to show the dropdown for choices
  window.showChoices = function(element) {
    // Get the field name and the choices for that field
    const fieldName = element.getAttribute('data-field');
    const choices = JSON.parse(element.getAttribute('data-choices'));

    // Create a new select element
    const select = document.createElement('select');
    select.setAttribute('name', fieldName);
    select.classList.add('dynamic-select');

    // Populate the select element with options
    choices.forEach(function(choice) {
      const option = document.createElement('option');
      option.value = choice[0];
      option.textContent = choice[1];
      select.appendChild(option);
    });

    // Position the select element
    select.style.position = 'absolute';
    select.style.left = element.getBoundingClientRect().left + 'px';
    select.style.top = element.getBoundingClientRect().bottom + 'px';

    // Handle selection of an option
    select.onchange = function() {
      // Update the display text
      element.textContent = this.options[this.selectedIndex].text;
      // Update the value of the corresponding hidden field
      document.querySelector('input[name="' + fieldName + '"]').value = this.value;
      // Remove the select element after selection
      document.body.removeChild(select);
    };

    // Add the select element to the body and focus it
    document.body.appendChild(select);
    select.focus();

    // Remove the select element if we click outside of it
    document.addEventListener('click', function(event) {
      if (event.target !== select) {
        if (select.parentNode) {
          select.parentNode.removeChild(select);
        }
      }
    }, { once: true });
  };
});
