/*
 * The theme toggle -- the only JavaScript the site adds besides htmx and Alpine.
 *
 * With no stored choice, site.css follows the system setting on its own. A
 * click stores "light" or "dark" and sets data-theme on <html>, which site.css
 * prefers over the system setting. The inline script in base.html's <head>
 * re-applies a stored choice before first paint, so this file can load late.
 *
 * Toggling back to the theme the system already uses stores nothing and
 * removes the attribute instead: the visitor is following their system again,
 * live, rather than pinned to a choice that happens to match it today. That
 * is the whole of the "back to system" behaviour -- there is no third state to
 * see or press (docs/ai/night-2026-09-16/questions.md Q3, answered by the
 * night-2026-09-17 plan).
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

  function systemTheme() {
    return system.matches ? "dark" : "light";
  }

  function shown() {
    return root.getAttribute("data-theme") || systemTheme();
  }

  function sync() {
    button.setAttribute("aria-pressed", String(shown() === "dark"));
  }

  button.addEventListener("click", function () {
    var next = shown() === "dark" ? "light" : "dark";
    var following = next === systemTheme();
    if (following) {
      root.removeAttribute("data-theme");
    } else {
      root.setAttribute("data-theme", next);
    }
    try {
      if (following) {
        window.localStorage.removeItem("theme");
      } else {
        window.localStorage.setItem("theme", next);
      }
    } catch (error) {
      // Storage refused (private mode, blocked site data). Either way the
      // page already shows what was asked for, and only this page: a choice
      // that could not be stored is gone on the next load, and a choice that
      // could not be removed comes back on it.
    }
    sync();
  });

  // With no stored choice, an operating-system switch changes the theme live
  // through CSS; keep the button's pressed state telling the truth.
  system.addEventListener("change", sync);

  sync();
  button.hidden = false;
})();
