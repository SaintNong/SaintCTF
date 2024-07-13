function checkHash() {
    // If the linked challenge is solved, all solved challenges are automatically shown
    const solved = $(location.hash).data("solved") !== undefined;
    if (solved) {
        // https://stackoverflow.com/a/426276
        $('[name="solved"]').prop('checked', true).trigger('change');

        // https://stackoverflow.com/a/62546650 (scrollIntoView)
        // https://stackoverflow.com/a/4884904 (jQuery usage)
        $(location.hash)[0].scrollIntoView(); // force challenge into view
    }
}

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
                        html: response.message,
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
                        html: response.message,
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

const effectOptions = {duration: 250, easing: "linear"};

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

    checkHash();
});

window.addEventListener("hashchange", checkHash);

titleTooltip('top'); // filter tags
absoluteTimeTooltip("time");

// view buttons
function switchView(id) {
    const full_id = `#challenge-${id}-view`;
    $(".view").not(full_id).hide();
    $(full_id).fadeIn(effectOptions);
}

// chart
let resetChartZoom;
let fullscreenChart;
$(document).ready(function () {
    const challengesDataset = {
        data: [],
        backgroundColor: [],
    };

    let averages = {};

    $(".challenge").each((i, e) => {
        const element = $(e);

        const points_regexp = /\d*/;

        const points = Number(points_regexp.exec(element.find(".points").text())[0]);
        const difficulty = element.data("difficulty");
        const category = element.data("category");

        challengesDataset.data.push({
            x: element.find("header > div > h2 > span").text(),
            y: points,

            author: element.find("header .author").text(),
            difficulty: difficulty,
            category: category,
        });

        challengesDataset.backgroundColor.push(element.css("borderLeftColor"));

        if (difficulty in averages) {
            averages[difficulty].push(points);
        } else {
            averages[difficulty] = [points];
        }
    });

    Object.keys(averages).forEach(diff => {
        averages[diff] = averages[diff].reduce((a, x) => a + x, 0) / averages[diff].length;
    })

    const averagesDataset = {
        type: 'line',
        data: [],
        stepped: 'middle',
        borderColor: "#FFFFFF",
        backgroundColor: "#343434",
        fill: 'origin',
        pointRadius: 0,
    };

    $(".challenge").each((i, e) => {
        const element = $(e);
        averagesDataset.data.push(averages[element.data("difficulty")]);
    })

    const ctx = document.getElementById('challenges-chart').getContext('2d');

    const challengesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            datasets: [challengesDataset, averagesDataset],
        },
        options: getChartOptions({
            scales: {
                x: {
                    type: 'category'
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        beforeBody: function(items) {
                            return items.map(item => item.raw.author);
                        },
                        afterBody: function(items) {
                            return items.map(item => item.raw.difficulty + ", " + item.raw.category);
                        }
                    }
                }
            }
        }),
    });

    resetChartZoom = challengesChart.resetZoom;
    fullscreenChart = () => {
        if (document.fullscreenElement === null) {
            $("#maximize-icon").hide();
            $("#minimize-icon").show();
            document.getElementById("chart-container").requestFullscreen();
        } else {
            $("#minimize-icon").hide();
            $("#maximize-icon").show();
            document.exitFullscreen();
        }
    };
});
