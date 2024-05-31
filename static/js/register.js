$(document).ready(function() {
    $('#signup-form').submit(function(e) {
        e.preventDefault();  // Prevent default form submission

        const formData = $(this).serialize();  // Serialize form data

        $.ajax({
            type: 'POST',
            url: '/register',
            data: formData,
            success: function(response) {
                if (response.status === 'success') {
                    // On successful signup we go straight to challenges
                    window.location.href = '/challenges'
                } else if (response.status === 'error') {
                    Swal.fire({
                        title: "Registration Failed!",
                        text: response.message,
                        icon: "error"
                    });
                }
            },
            error: function(xhr, status, error) {
                // Handler if AJAX itself fails (network issues, etc.)
                Swal.fire({
                    title: "Error",
                    text: "Something went wrong: " + error,
                    icon: "error"
                });
            }
        });
    });
});
