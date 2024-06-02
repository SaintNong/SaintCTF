// Data attribute from <script> tag
// https://stackoverflow.com/a/22745553
const currentUsername = document.currentScript.dataset.username;
const leaderboardEvents = new EventSource("leaderboard-events");

$(document).ready(function () {
    function divmod(a, b) {
        return [Math.floor(a/b), a % b];
    }

    function time_ago(time) {
        const delta = new Date() - time;
        let day, hour, minute, second, remainder;
        [day, remainder] = divmod(delta, (1000 * 60 * 60 * 24));
        [hour, remainder] = divmod(remainder, (1000 * 60 * 60));
        [minute, remainder] = divmod(remainder, (1000 * 60));
        [second, remainder] = divmod(remainder, (1000));

        if (day > 0) {
            return `${day} day${day > 1 ? 's' : ''} ${hour} hour${hour > 1 ? 's' : ''} ago`
        } else if (hour > 0) {
            return `${hour} hour${hour > 1 ? 's' : ''} ${minute} minute${minute > 1 ? 's' : ''} ago`
        } else if (minute > 0) {
            return `${minute} minute${minute > 1 ? 's' : ''} ago`
        } else if (second > 5) {
            return `${second} seconds ago`
        } else {
            return "Just now"
        }
    }

    // Periodically update relative times
    setInterval(function () {
        $("time").each(function () {
            const element = $(this);
            element.text(time_ago(new Date(element.attr("datetime"))));
        });
    }, 2500);

    leaderboardEvents.addEventListener("leaderboard", (event) => {
        const data = JSON.parse(event.data);

        // Nuke the old leaderboard
        let leaderboard = $("#leaderboard");
        leaderboard.empty();

        // Make header
        leaderboard.append(`<thead> <tr><th style="width: 50px;">Rank</th> <th>Name</th> <th>Score</th></tr> </thead>`);


        // Rebuild the leaderboard
        let tbody = $("<tbody></tbody>");
        $.each(data, function (index, user) {
            // Check if the user is the current user, and highlight if they are
            let highlight = user.username === currentUsername ? 'class="highlight" id="current-user"' : '';
            tbody.append(`<tr ${highlight}><td>${index + 1}</td><td id="username-data"><a href="/profile/${user.user_id}">${user.username}</a></td><td>${user.score}</td></tr>`);

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

            const first_blood = solve.first_blood ? ' title="First blood">🏆' : ">";

            tbody.append(`<tr ${highlight}><td>${solve.solver}</td><td${first_blood}</td><td>${solve.challenge.name}</td><td><time datetime="${solve.time}">${relative_time}</time></td></tr>`);
        });
        recentTable.append(tbody);
    });
});

$(document).ready(function () {
    const ctx = document.getElementById('leaderboard-chart').getContext('2d');
    let leaderboardChart;

    leaderboardEvents.addEventListener("chart", (event) => {
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
        }
    }
});
