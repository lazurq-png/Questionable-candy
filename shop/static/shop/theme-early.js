/*
 * 500.html's copy of the inline script in base.html's <head>: re-applies a
 * stored theme choice before first paint. A file rather than inline because
 * the Content-Security-Policy refuses an inline script without a nonce, and
 * 500.html renders with no request to take one from. Load it without defer,
 * before the stylesheet, or a dark choice flashes light.
 */
(function () {
    try {
        var theme = window.localStorage.getItem("theme");
        if (theme === "light" || theme === "dark") {
            document.documentElement.setAttribute("data-theme", theme);
        }
    } catch (error) {}
})();
