// Data attribute from <script> tag
// https://stackoverflow.com/a/22745553
const currentUsername = document.currentScript.dataset.username;
const leaderboardEvents = new EventSource("leaderboard-events");

// Show a loading toast until SSE has loaded any data
// https://github.com/sweetalert2/sweetalert2/issues/2508#issuecomment-1263293979 (prevent toast from being dismissed)
Swal.fire({
    toast: true,
    position: 'top-end',

    showConfirmButton: false,
    showCloseButton: true,
    customClass: {
        closeButton: 'toast-hidden',
    },

    title: "Loading...",
    didOpen: () => {
        Swal.showLoading();
    }
});

$(document).ready(function () {
    leaderboardEvents.addEventListener("leaderboard", (event) => {
        if (Swal.isLoading()) {
            Swal.close(); // Dismiss any loading toasts
        }

        const data = JSON.parse(event.data);

        // Nuke the old leaderboard
        let leaderboard = $("#leaderboard");
        leaderboard.empty();

        // Make header
        leaderboard.append(`<thead> <tr><th class="number-col">Rank</th> <th class="expand">Name</th> <th class="number-col">Score</th></tr> </thead>`);


        // Rebuild the leaderboard
        let tbody = $("<tbody></tbody>");
        $.each(data, function (index, user) {
            // Check if the user is the current user, and highlight if they are
            let highlight = user.username === currentUsername ? 'class="highlight" id="current-user"' : '';
            let trophy = "";
            if (index < 3) {
                const icons = ["🥇","🥈","🥉"];
                trophy = `<span>${icons[index]}</span>`;
            }
            tbody.append(`<tr ${highlight}><td class="number-col">${trophy}${index + 1}</td><td class="username-data"><a href="/profile/${user.id}">${user.username}</a></td><td class="number-col">${user.score}</td></tr>`);

        });
        leaderboard.append(tbody);
    });

    leaderboardEvents.addEventListener("recentActivity", (event) => {
        if (Swal.isLoading()) {
            Swal.close(); // Dismiss any loading toasts
        }

        const data = JSON.parse(event.data);

        let recentTable = $("#recent-table");
        // Clear the old content
        recentTable.empty();

        // Define the table headers
        recentTable.append(`<thead><tr><th>Solver</th><th></th><th>Challenge</th><th>Time</th></tr></thead>`);

        // Append data to the table body
        let tbody = $("<tbody></tbody>");
        $.each(data, function (index, solve) {
            // Check if the user is the current user, and highlight if they are
            let highlight = solve.solver === currentUsername ? 'class="highlight"' : '';

            const relative_time = time_ago(new Date(solve.time));

            const first_blood = solve.first_blood ? '<span title="First blood">🏆</span>' : "";

            tbody.append(`<tr ${highlight}><td><a href="/profile/${solve.solver_id}">${solve.solver}</a></td><td>${first_blood}</td><td><a href="/challenges#${solve.challenge_id}">${solve.challenge_name}</a></td><td><time datetime="${solve.time}">${relative_time}</time></td></tr>`);
        });
        recentTable.append(tbody);

        absoluteTimeTooltip("time");
        titleTooltip('right'); // first blood
    });
});

let resetChartZoom;
let fullscreenChart;

$(document).ready(function () {
    const ctx = document.getElementById('leaderboard-chart').getContext('2d');
    let leaderboardChart;

    leaderboardEvents.addEventListener("chart", (event) => {
        if (Swal.isLoading()) {
            Swal.close(); // Dismiss any loading toasts
        }

        const chartData = formatChartData(JSON.parse(event.data));
        renderChart(chartData);
    });

    function formatChartData(rawData) {
        const datasets = {};
        rawData.forEach(item => {
            if (!datasets[item.user]) {
                let color = getUserColor(item.user);

                datasets[item.user] = {
                    label: item.user,
                    data: [],
                    borderColor: color,
                    backgroundColor: color,
                    fill: false, // andrew what this do explain plz
                    stepped: "before"
                };
            }
            datasets[item.user].data.push({
                x: item.time,
                y: item.points
            });
        });

        return Object.values(datasets);
    }


    function updateChart(newData) {
        newData.forEach(function(newDataset, i) {
            $.extend(leaderboardChart.data.datasets[i], newDataset);
        });

        leaderboardChart.update();
    }

    function renderChart(data) {
        if (leaderboardChart) {
            updateChart(data);
        } else {
            leaderboardChart = new Chart(ctx, {
                type: 'line',
                data: {
                    datasets: data
                },
                options: getChartOptions()
            });

            resetChartZoom = leaderboardChart.resetZoom;
            fullscreenChart = () => {
                if (document.fullscreenElement === null) {
                    $("#maximize-icon").hide();
                    $("#minimize-icon").show();
                    document.getElementById("leaderboard-chart-container").requestFullscreen();
                } else {
                    $("#minimize-icon").hide();
                    $("#maximize-icon").show();
                    document.exitFullscreen();
                }
            };
        }
    }
});
