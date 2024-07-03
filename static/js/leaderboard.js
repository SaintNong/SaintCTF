// Data attribute from <script> tag
// https://stackoverflow.com/a/22745553
const currentUsername = document.currentScript.dataset.username;
const leaderboardEvents = new EventSource("leaderboard-events");

$(document).ready(function () {
    leaderboardEvents.addEventListener("leaderboard", (event) => {
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

            tbody.append(`<tr ${highlight}><td><a href="/profile/${solve.solver_id}">${solve.solver}</a></td><td>${first_blood}</td><td><a href="/challenges#${solve.challenge_id}">${solve.challenge.name}</a></td><td><time datetime="${solve.time}">${relative_time}</time></td></tr>`);
        });
        recentTable.append(tbody);

        absoluteTimeTooltip("time");
        titleTooltip('right'); // first blood
    });
});

$(document).ready(function () {
    let leaderboardChart;

    leaderboardEvents.addEventListener("chart", (event) => {
        const chartData = formatChartData(JSON.parse(event.data));
        renderChart(chartData);
    });

    function formatChartData(rawData) {
        const data = {};
        rawData.forEach(item => {
            if (!data[item.user]) {
                let color = getUserColor(item.user);

                data[item.user] = {
                    name: item.user,
                    x: [],
                    y: [],
                    marker: {
                        color: color,
                    },
                    line: {
                        shape: "hv" // "hold value"
                    }
                };
            }
            data[item.user].x.push(item.time);
            data[item.user].y.push(item.points);
        });

        return Object.values(data);
    }

    function renderChart(data) {
        let func;
        if (leaderboardChart) {
            func = Plotly.react;
        } else {
            func = Plotly.newPlot;
        }
        leaderboardChart = func("leaderboard-chart-container", data, ...getChartOptions());
    }
});
