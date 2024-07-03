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

$(document).ready(function() {
    let userColor = getUserColor(username);

    let chart = Plotly.newPlot("chart-container", [{
        name: username,
        x: times,
        y: points,
        marker: {
            color: userColor
        },
        line: {
            shape: "hv" // "hold value"
        }
    }], ...getChartOptions());
});
