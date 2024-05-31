// OH MY GOD ITS JQUERY RUNNNNNN
$(document).ready(function () {
    $('#flag-form').submit(function (e) {
        // Prevents default ugly form submission
        e.preventDefault();

        // Extract data
        let form = $(this);

        $.ajax({
            type: 'POST',
            url: '/submit-flag',
            data: form.serialize(), // Pass the form data to the endpoint

            // When the response comes back
            success: function (response) {
                console.log(response)

                // If the flag was correct
                if (response.status === 'correct') {
                    // Correct alert
                    Swal.fire({
                        title: "Correct flag!",
                        text: response.message,
                        icon: "success"

                    }).then(
                        function () {
                            // Reload page after the user dismisses the alert
                            // This is to update the solved challenges and user score
                            window.location.reload()
                        }
                    );


                } else if (response.status === 'already_submitted') {
                    // Already submitted alert
                    Swal.fire({
                        title: "Already submitted!",
                        text: response.message,
                        icon: "warning"
                    });

                } else {
                    // Wrong alert
                    Swal.fire({
                        title: "Wrong flag!",
                        text: response.message,
                        icon: "error"
                    });
                }

            },

            // After its all done, we clear the flag input field
            complete: function (data) {
                let input = $('#flag')
                input.val('');
            }
        });
    });
});


$(document).ready(function () {
    const filters = ['category', 'difficulty'];

    // Script for challenge filtering
    $('#filter-form').on("change", function (e) {
        // Values of the selected filters
        const selectedFilters = filters.map((f) => $(`[name="${f}"]`).val());
        const showSolved = $('[name="solved"]').prop('checked');

        let visibleCount = 0;
        $('.challenge').each(function () {
            const challenge = $(this);

            challenge.stop(true, false); // Clear queue of animations, but do not jump to end of current animation.

            // Whether or not the selected filters matches the challenge card's attributes
            const matchesFilters = filters.map((f, i, filters) => {
                const sf = selectedFilters[i]; // selected filter
                return sf === "" || challenge.data(f) === sf;
            });
            const matchesUnsolved = challenge.data('solved') === undefined;

            const effectOptions = {duration: 250, easing: "linear"};

            if (matchesFilters.every((x) => x) && (matchesUnsolved || showSolved)) {
                // If a matched filter is not "All <filter type>", highlight it
                //   i.e. only an explicitly selected filter should be highlighted
                filters.forEach((f, i, filters) => {
                    const value = selectedFilters[i] !== "" ? true : null;
                    challenge.find(`.filter-tag[data-filter-type=${f}]`).attr('data-selected', value);
                });

                challenge.slideDown(effectOptions);
                visibleCount++;
            } else {
                challenge.find(".filter-tag").attr('data-selected', null);
                challenge.slideUp(effectOptions);
            }
        });

        $("#visible-count").html(visibleCount);
    });

    // Setup filtering tags
    function setupFilteringTags(filterType) {
        $(`.filter-tag[data-filter-type=${filterType}]`).on('click', function (e) {
            // https://stackoverflow.com/a/10086501 Why `currentTarget`?
            const state = e.currentTarget.innerText;
            const stateSelectField = $(`[name="${filterType}"]`)
            if (stateSelectField.val() === state) {
                stateSelectField.val('').trigger('change');
            } else {
                stateSelectField.val(state).trigger('change');
            }
        });
    }

    filters.forEach((f) => setupFilteringTags(f));
});

