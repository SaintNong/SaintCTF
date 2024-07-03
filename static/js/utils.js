function time_ago(time) {
    function divmod(a, b) {
        return [Math.floor(a/b), a % b];
    }

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

function getChartOptions() {
    /*const traceX = data.flatMap((trace) => trace.x).sort();
    const traceY = data.flatMap((trace) => trace.y).sort((a, b) => a - b);*/
    const layout = {
        paper_bgcolor: '#121212',
        plot_bgcolor: '#121212',
        margin: {
            b: 40,
            l: 80,
            r: 80,
            t: 0,
        },
        font: {
            color: '#FFFFFF'
        },
        xaxis: {
            /*maxallowed: (new Date(traceX[0])).getTime(),
            minallowed: (new Date(traceX[traceX.length - 1])).getTime(),*/
            tickcolor: '#FFFFFF',
            gridcolor: 'rgba(255,255,255,0.1)'
        },
        yaxis: {
            minallowed: 0,
            /*maxallowed: traceY[traceY.length - 1],*/
            tickcolor: '#FFFFFF',
            gridcolor: 'rgba(255,255,255,0.1)',
            title: {
                text: 'Score'
            }
        },
    };

    const config = {
        responsive: true,
        scrollZoom: true,
    };

    return [layout, config];
}

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

const fmt = new Intl.DateTimeFormat(undefined, {
    dateStyle: "long",
    timeStyle: "medium"
});

// Show tooltip for elements with `title` attribute
function titleTooltip(placement) {
    tippy("[title]", {
        content(reference) {
            const title = reference.getAttribute('title');
            reference.removeAttribute('title');
            return title;
        },
        delay: [250, null],
        placement: placement
    });
}

// Show absolute time in tooltip
function absoluteTimeTooltip(o) {
    tippy(o, {
        content(reference) {
            const date = new Date(reference.getAttribute("datetime"));
            return fmt.format(date);
        },
        delay: [250, null],
        placement: 'top',
    });
}

$(document).ready(function () {
    // Periodically update relative times
    setInterval(function () {
        $("time").each(function () {
            const element = $(this);
            element.text(time_ago(new Date(element.attr("datetime"))));
        });
    }, 2500);

    // Show username colour in border when input changes
    $('input[name="username"]').on('input', (e) => {
        e.target.style.setProperty("--color", getUserColor(e.target.value));
        e.target.style.setProperty("--width", e.target.value.length !== 0
            ? "var(--width-present)" : "var(--width-empty)");
    });
});
