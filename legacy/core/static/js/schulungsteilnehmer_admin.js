function populateFields(select) {
    var row = select.closest('tr');
    var personId = select.value;
    if (personId) {
        fetch('/admin/get_person_details/' + personId + '/')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                var vornameField = row.querySelector('input[name$="-vorname"]');
                var nachnameField = row.querySelector('input[name$="-nachname"]');
                var emailField = row.querySelector('input[name$="-email"]');
                if (vornameField) vornameField.value = data.vorname || '';
                if (nachnameField) nachnameField.value = data.nachname || '';
                if (emailField) emailField.value = data.email || '';
            })
            .catch(error => {
                console.error('Error fetching person details:', error);
            });
    }
    // Do NOT clear fields when person is deselected - preserve existing data
}