function populateFields(select) {
    var row = select.closest('tr');
    var personId = select.value;
    if (personId) {
        fetch('/admin/get_person_details/' + personId + '/')
            .then(response => response.json())
            .then(data => {
                row.querySelector('input[name$="-vorname"]').value = data.vorname;
                row.querySelector('input[name$="-nachname"]').value = data.nachname;
                row.querySelector('input[name$="-email"]').value = data.email;
            });
    } else {
        row.querySelector('input[name$="-vorname"]').value = '';
        row.querySelector('input[name$="-nachname"]').value = '';
        row.querySelector('input[name$="-email"]').value = '';
    }
}