// Handle flashed messages passed via custom data attribute
const messages = JSON.parse(document.currentScript.dataset.messages);
for (const message of messages) {
    $(document).ready(function() {
        Swal.fire({
            title: message,
            icon: "info"
        });
    });
}


$(document).ready(function() {
    $('#login-form').submit(function(e) {
        e.preventDefault();  // Prevent default form submission

        const formData = $(this).serialize();  // Serialize form data

        $.ajax({
            type: 'POST',
            url: '/login',
            data: formData,
            success: function(response) {
                if (response.status === 'success') {
                    // On successful login we go straight to challenges
                    window.location.href = '/challenges'
                } else if (response.status === 'error') {
                    Swal.fire({
                        title: "Login Failed!",
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
