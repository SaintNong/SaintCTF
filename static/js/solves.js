titleTooltip('right'); // first blood
absoluteTimeTooltip("time");

let resetChartZoom;
let fullscreenChart;
$(document).ready(function () {
    const solves = {};

    $("#scroll-container tbody tr").each((i, e) => {
        const element = $(e);

        const name = element.children()[2].innerText;
        if (name in solves === false) {
            solves[name] = {
                y: 0,
                category: element.children()[3].innerText,
                difficulty: element.children()[4].innerText,
            };
        }
        solves[name]['y'] += 1;
    });

    // Sort challenges by number of solves descending, and take top 10
    const data = Object.entries(solves).map(x => ({x: x[0], ...x[1]})).sort((a, b) => b['y'] - a['y']).slice(0, 10);
    const dataset = {
        data: data,
        backgroundColor: data.map(x => getUserColor(x['x'])),
    };

    const ctx = document.getElementById('solves-chart').getContext('2d');
    const solvesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            datasets: [dataset],
        },
        options: getChartOptions({
            scales: {
                x: {
                    type: 'category'
                },
                y: {
                    ticks: {
                        stepSize: 1
                    },
                    title: {
                        text: 'Solves'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        afterBody: function(items) {
                            return items.map(item => item.raw.difficulty + ", " + item.raw.category);
                        }
                    }
                }
            }
        }),
    });

    resetChartZoom = solvesChart.resetZoom;
    fullscreenChart = () => {
        if (document.fullscreenElement === null) {
            $("#maximize-icon").hide();
            $("#minimize-icon").show();
            document.getElementById("solves-chart-container").requestFullscreen();
        } else {
            $("#minimize-icon").hide();
            $("#maximize-icon").show();
            document.exitFullscreen();
        }
    };
});
