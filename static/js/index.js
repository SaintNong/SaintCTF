$('#flag-form').submit(function (e) {
    e.preventDefault();

    Swal.fire({
        title: "Correct flag!",
        html: "You've earned 20 points for <code>My First Challenge!</code>.",
        icon: "success",
        footer: "This <strong>example alert</strong> tells you how many points you've earned by completing a challenge."
    });
});


$('#flag-form-incorrect').submit(function (e) {
    e.preventDefault();

    Swal.fire({
        title: "Wrong flag!",
        text: "Incorrect flag. Try again!",
        icon: "error",
        footer: "This <strong> example alert</strong> tells you that you should keep trying &mdash; you are not penalised for this action."
    });
});

function tagClickHandler(e) {
    const tag = $(e.currentTarget);
    const selected = tag.attr('data-selected') !== undefined;

    if (selected) {
        tag.attr('data-selected', null);
    } else {
        tag.attr('data-selected', true);
    }
}

$("#difficulty-tag").on('click', tagClickHandler);
$("#category-tag").on('click', tagClickHandler);
