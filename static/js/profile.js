// Prepare data for the score chart
const username = document.currentScript.dataset.username;
const datapoints = JSON.parse(document.currentScript.dataset.datapoints);
let times = [];
let points = [];

for (const datapoint of datapoints) {
    times.push(datapoint.time);
    points.push(datapoint.points);
}

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
});
