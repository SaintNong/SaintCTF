tippy("[title]", {
    content(reference) {
        const title = reference.getAttribute('title');
        reference.removeAttribute('title');
        return title;
    },
    delay: [250, null],
    placement: 'right',
});
absoluteTimeTooltip("time");
