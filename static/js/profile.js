absoluteTimeTooltip("time");
titleTooltip('right'); // first blood

// Prepare data for the score chart
const username = document.currentScript.dataset.username;
const datapoints = JSON.parse(document.currentScript.dataset.datapoints);
let times = [];
let points = [];

for (const datapoint of datapoints) {
    times.push(datapoint.time);
    points.push(datapoint.points);
}

let resetChartZoom;

$(document).ready(function() {
    let userColor = getUserColor(username);


    let ctx = document.getElementById('score-history').getContext('2d');
    let chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: times,
            datasets: [{
                label: username,
                data: points,
                stepped: "before",

                backgroundColor: userColor,
                borderColor: userColor,

                fill: false,
            }]
        },
        options: getChartOptions({
            plugins: {
                legend: {
                    // Disable legend click behaviour
                    // https://github.com/chartjs/Chart.js/issues/2190#issuecomment-203444324
                    onClick: (event, legendItem, legend) => {}
                }
            },
        })
    });

    resetChartZoom = chart.resetZoom;
});

// Prepare data for the solve chart
let solve_categories = {};
let solve_difficulties = {};

for (const datapoint of datapoints) {
    if (datapoint.category === undefined || datapoint.difficulty === undefined)
        continue;

    if (datapoint.category in solve_categories === false) {
        solve_categories[datapoint.category] = 0;
    }
    solve_categories[datapoint.category] += 1;

    if (datapoint.difficulty in solve_difficulties === false) {
        solve_difficulties[datapoint.difficulty] = 0;
    }
    solve_difficulties[datapoint.difficulty] += 1;
}

const solve_labels = Object.keys(solve_categories).concat(Object.keys(solve_difficulties));
const solve_colours = solve_labels.map(x => getUserColor(x));

let solve_categories_data = solve_labels.map(x => solve_categories[x] || 0);
let solve_difficulties_data = solve_labels.map(x => solve_difficulties[x] || 0);

// https://github.com/chartjs/Chart.js/issues/3953#issuecomment-813233583
$(document).ready(function() {
    const element = document.getElementById('solve-chart');
    if (element === null)
        return;

    let ctx = element.getContext('2d');
    let chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: solve_labels,
            datasets: [{
                title: "Categories",
                data: solve_categories_data,
                backgroundColor: solve_colours,
            }, {
                title: "Difficulties",
                data: solve_difficulties_data,
                backgroundColor: solve_colours,
            }]
        },
        options: getChartOptions({
            scales: {
                x: {
                    type: 'category',
                    title: {
                        display: false,
                    },
                    grid: {
                        display: false,
                    },
                    ticks: {
                        display: false,
                    }
                },
                y: {
                    type: 'category',
                    title: {
                        display: false,
                    },
                    grid: {
                        display: false,
                    },
                    ticks: {
                        display: false,
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        title: function(items) {
                            return items.map(item => item.dataset.title + ":");
                        },
                    }
                }
            },
            // https://github.com/chartjs/Chart.js/issues/6545#issuecomment-1111987275
            onResize: function(chart, size) {
                if (size.width / size.height > 1.33) {
                    chart.options.plugins.legend.position = "right";
                } else {
                    chart.options.plugins.legend.position = "top";
                }
                chart.update();
            }
        })
    });
});
