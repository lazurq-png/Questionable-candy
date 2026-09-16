/*
 * The theme toggle -- the only JavaScript the site adds besides htmx and Alpine.
 *
 * With no stored choice, site.css follows the system setting on its own. A
 * click stores "light" or "dark" and sets data-theme on <html>, which site.css
 * prefers over the system setting. The inline script in base.html's <head>
 * re-applies a stored choice before first paint, so this file can load late.
 *
 * The button ships hidden and is revealed here, so a visitor without
 * JavaScript never sees a control that cannot work.
 */
(function () {
  "use strict";

  var root = document.documentElement;
  var system = window.matchMedia("(prefers-color-scheme: dark)");
  var button = document.querySelector("[data-theme-toggle]");
  if (!button) {
    return;
  }

  function shown() {
    return root.getAttribute("data-theme") || (system.matches ? "dark" : "light");
  }

  function sync() {
    button.setAttribute("aria-pressed", String(shown() === "dark"));
  }

  button.addEventListener("click", function () {
    var next = shown() === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try {
      window.localStorage.setItem("theme", next);
    } catch (error) {
      // Storage refused (private mode, blocked site data): the choice lasts
      // for this page only, which is still better than a toggle that fails.
    }
    sync();
  });

  // With no stored choice, an operating-system switch changes the theme live
  // through CSS; keep the button's pressed state telling the truth.
  system.addEventListener("change", sync);

  sync();
  button.hidden = false;
})();
