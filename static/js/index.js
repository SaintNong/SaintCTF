$('#flag-form').submit(function (e) {
    // Prevents default ugly form submission
    e.preventDefault();

    // Extract data
    let form = $(this);
    Swal.fire({
        title: "Correct flag!",
        html: "You've earned 20 points for <code>My First Challenge!</code>.",
        icon: "success",
        footer: "This alert tells you how many points you've earned by completing a challenge."
    });
});


$('#flag-form-incorrect').submit(function (e) {
    e.preventDefault();

    Swal.fire({
        title: "Wrong flag!",
        text: "Incorrect flag. Try again!",
        icon: "error",
        footer: "This alert tells you that you should keep trying &mdash; you are not penalised for this action."
    });
});
