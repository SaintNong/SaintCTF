// Capture redirects to this page
// https://stackoverflow.com/a/17877279
if (document.currentScript.dataset.login_msg !== undefined) {
    $(document).ready(function() {
        Swal.fire({
            title: "You have to log in to do that!",
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
