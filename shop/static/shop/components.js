/*
 * The behaviour the templates' Alpine and htmx attributes used to spell out
 * inline, for a Content-Security-Policy without 'unsafe-eval' (ADR 0006,
 * amended 2026-11-17).
 *
 * Neither library may turn attribute text into code any more. Alpine's CSP
 * build parses simple expressions itself -- names, literals, !, &&, ===, a
 * call to a component's method -- but not function definitions, globals such
 * as document or setTimeout, or statements joined with ";". htmx is told not
 * to evaluate at all (the htmx-config meta tag in base.html). So:
 *
 * - each x-data that needed more than that names a component registered
 *   here, and its attributes name the component's properties and methods;
 * - the two hx-on handlers and the one hx-trigger filter are plain listeners
 *   at the bottom of this file.
 *
 * An attribute that still fits the parser (x-bind:hidden="!cartOpen", the
 * cart stepper's x-data) stays where it is.
 *
 * Loaded with defer, before Alpine, so the components are registered by the
 * time Alpine starts (alpine:init), and before DOMContentLoaded, when htmx
 * processes the page.
 */
(function () {
  "use strict";

  function refreshCart() {
    document.body.dispatchEvent(new CustomEvent("shoppingcart-refresh", { bubbles: true }));
  }

  document.addEventListener("alpine:init", function () {
    var Alpine = window.Alpine;

    // The cart dropdown, on <body> (base.html). Its toggle is in the header
    // (shoppingcart_link.html), its close button in the panel
    // (shoppingcart_panel.html); the candy popup <dialog> is in its scope too.
    Alpine.data("site", function () {
      return {
        cartOpen: false,

        toggleCart: function () {
          this.cartOpen = !this.cartOpen;
          if (this.cartOpen) {
            refreshCart();
          }
        },

        // A response announced that the cart changed: reload the panel, but
        // only while it is open (views.shoppingcart_panel).
        refreshCartIfOpen: function () {
          if (this.cartOpen) {
            refreshCart();
          }
        },

        closeCart: function () {
          this.cartOpen = false;
          document.getElementById("shoppingcart-link").focus();
        },

        // Escape closes the dropdown -- unless the detail popup is open,
        // whose Escape closes only itself.
        closeCartOnEscape: function () {
          if (this.cartOpen && !document.querySelector("dialog[open]")) {
            this.closeCart();
          }
        },

        // The toggle is a link with role="button", so Space must press it.
        pressWithSpace: function (event) {
          event.currentTarget.click();
        },

        // A click on the backdrop lands on the <dialog> itself, since its
        // contents fill it.
        closePopupOnBackdrop: function (event) {
          if (event.target === event.currentTarget) {
            event.currentTarget.close();
          }
        },
      };
    });

    // The last step of checkout (checkout_confirm.html): the button stays
    // disabled until the box is ticked and the typed total equals the order's.
    // The server checks the same; this only saves a round trip.
    Alpine.data("confirmOrder", function () {
      return {
        checked: false,
        typed: "",
        total: "",

        init: function () {
          var data = this.$el.dataset;
          this.checked = data.checked === "true";
          this.typed = data.typed;
          this.total = data.total;
        },

        matches: function () {
          var typed = this.typed.trim().replace(/^\$/, "").trim().replace(",", ".");
          return typed !== "" && !Number.isNaN(Number(typed)) && Number(typed) === Number(this.total);
        },
      };
    });

    // A flash message that fades out after five seconds (profile.html).
    Alpine.data("flash", function () {
      return {
        shown: true,

        init: function () {
          var self = this;
          setTimeout(function () {
            self.shown = false;
          }, 5000);
        },
      };
    });
  });

  // The candy popup opens when a candy link's details are swapped into it --
  // only a swap into the contents themselves, not the stepper swaps that
  // happen inside it once open. (Was hx-on:htmx:after-swap on the <dialog>.)
  document.addEventListener("htmx:afterSwap", function (event) {
    var popup = document.getElementById("candy-popup");
    if (popup && event.detail.target.id === "candy-popup-contents" && !popup.open) {
      popup.showModal();
    }
  });

  // A cart stepper keeps focus in its own field while its form is sent, so a
  // keyboard user is not dropped when the stepper is swapped. Only the form's
  // own submit, not its - and + buttons. (Was hx-on:htmx:before-request on
  // the form, cart_stepper.html.)
  document.addEventListener("htmx:beforeRequest", function (event) {
    var form = event.detail.elt;
    if (form.matches && form.matches("form.cart-stepper")) {
      form.elements.quantity.focus();
    }
  });

  // The cart page reloads its list when the cart changed from inside the
  // candy popup; changes on the page itself already swap the list.
  // shoppingcart.html listens for the event sent here. (Was the filter
  // [!!event.target.closest('#candy-popup')] on its hx-trigger.)
  document.addEventListener("shoppingcart-changed", function (event) {
    if (event.target.closest && event.target.closest("#candy-popup")) {
      document.body.dispatchEvent(new CustomEvent("shoppingcart-changed-in-popup"));
    }
  });
})();
