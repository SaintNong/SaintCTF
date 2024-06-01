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
        options: {
            scales: {
                x: {
                    type: 'time',
                    ticks: {
                        color: '#FFFFFF' // White color for ticks
                    },
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#FFFFFF', // White color for ticks
                    },
                    grid: {
                        color: 'rgba(255,255,255,0.1)' // Lighter grid lines against a dark background
                    },
                    title: {
                        display: true,
                        text: 'Score',
                        color: '#FFFFFF' // Ensuring the title is also white
                    }
                }
            },
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#FFFFFF' // White color for legend text
                    },
                    // Disable legend click behaviour
                    // https://github.com/chartjs/Chart.js/issues/2190#issuecomment-203444324
                    onClick: (event, legendItem, legend) => {}
                }
            },
            layout: {
                padding: {
                    x: 20,
                    y: 0
                }
            },
            backgroundColor: '#333333'
        }
    });
});

// Gets a predictable user color for each username
function getUserColor(username) {
    let color = '#';
    let seed = 0;

    // Go through the username and do some bit flipping and flopping
    for (let i = 0; i < username.length; i++) {
        seed = username.charCodeAt(i) + ((seed << 6) + 2 * seed);

        // XOR shift
        seed ^= seed >> 7;
        seed ^= seed << 11;
        seed ^= seed << 17;
    }

    // 3 hex values
    for (let i = 0; i < 3; i++) {
        // Flip-flop around some more
        let value = (seed >> i) & 0xFF;

        // Convert the number to hex
        color += ('00' + value.toString(16)).slice(-2);
    }

    // If the color is too dark, run the hash function again
    if (isDark(color)) {
        return getUserColor(username + 'a');
    }

    // And our color is created!
    return color;
}

// Credit: https://stackoverflow.com/questions/596216/formula-to-determine-perceived-brightness-of-rgb-color
function isDark(hex) {
    const r = parseInt(hex.slice(1, 3), 16) / 255;
    const g = parseInt(hex.slice(3, 5), 16) / 255;
    const b = parseInt(hex.slice(5, 7), 16) / 255;

    // Calculate perceived luminance according to ITU-R BT.709
    const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
    console.log(luminance);
    if (luminance < 0.4) {
        console.log("Retrying");
    }
    return luminance < 0.3;
}


