// The order admin's lines (shop/templates/shop/admin/order_item_tabular.html).
//
// A saved line's candy name opens the candy's details in a dialog
// (candy_details_widget.html). A green plus in the ORDER ITEMS bar opens a
// dialog to choose a candy and a quantity; choosing saves the order with that
// line added, through the same save as the page's own buttons. Escape closes
// either dialog natively; so do Cancel/Close and a click on the backdrop.
// Closing returns focus to whatever opened it.
//
// This replaces Django's admin/js/inlines.js for these lines (shop/admin.py,
// OrderItemInline.media): no row is ever added in the page, so nothing needs
// its "Add another" row or remove buttons.

// A save that comes back to this order ("Save and continue editing", which
// the add dialog uses too, or a save refused with errors) reloads the page,
// which would start at the top. So the lines' position on screen is kept
// across it -- the lines rather than the scroll offset, because the reloaded
// page gains a message at the top that pushes everything down.
const SCROLL_KEY = "order-admin-lines-top";

document.addEventListener("submit", (event) => {
  const lines = document.getElementById("items-group");
  if (lines && event.target.matches("#order_form") && event.submitter?.name === "_continue") {
    try {
      sessionStorage.setItem(SCROLL_KEY, String(lines.getBoundingClientRect().top));
    } catch {
      // No storage (private window, blocked site data): the page starts at the top.
    }
  }
});

// The add dialog opens from a green plus at the right of the ORDER ITEMS bar.
// Only where lines may be added: Django renders the row template only then.
document.addEventListener("DOMContentLoaded", () => {
  const heading = document.getElementById("items-heading");
  if (!heading || !document.getElementById("items-empty")) {
    return;
  }
  const add = document.createElement("button");
  add.type = "button";
  add.className = "order-lines-add";
  add.setAttribute("aria-label", "Add another Order item");
  add.title = "Add another Order item";
  add.addEventListener("click", openAddDialog);
  heading.append(add);
});

// A saved line's "Delete?" checkbox becomes a red X. Confirmed in a dialog, it
// ticks the checkbox and saves at once -- the same save as ticking it and
// pressing a save button, so stock and the total follow. Without this script
// the checkbox stays.

// The checkbox of the line the remove dialog is asking about.
let removing = null;

function removeDialog() {
  return document.getElementById("items-remove-dialog");
}

function askToRemove(box) {
  removing = box;
  const title = box.closest("tr").querySelector(".candy-line-title");
  document.getElementById("items-remove-text").textContent =
    `Remove ${title ? title.textContent.replace(/\s+/g, " ").trim() : "this line"} from the order? ` +
    "The order is saved at once.";
  removeDialog().showModal();
  // Cancel first, so an Enter pressed out of habit removes nothing.
  removeDialog().querySelector("[data-close-dialog]").focus();
}

function confirmRemove() {
  const box = removing;
  removeDialog().close();
  if (box) {
    box.checked = true;
    saveOrder();
  }
}
function saveOrder() {
  const form = document.getElementById("order_form");
  // As "Save and continue editing" would, staying on the order's page.
  form.requestSubmit(form.querySelector('input[name="_continue"]'));
}

document.addEventListener("DOMContentLoaded", () => {
  const boxes = document.querySelectorAll('#items-group td.delete input[type="checkbox"]');
  for (const box of boxes) {
    const name = box.closest("tr").querySelector(".candy-line-title button")?.textContent;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "order-lines-remove";
    remove.setAttribute("aria-label", name ? `Remove ${name}` : "Remove this line");
    remove.title = remove.getAttribute("aria-label");
    remove.addEventListener("click", () => askToRemove(box));
    box.hidden = true;
    box.after(remove);
  }
  if (boxes.length) {
    document.querySelector("#items-group thead th:last-child").textContent = "";
  }
});

// The page's messages show as a popup (order_item_tabular.html). Each gets a
// close button; a success or info message also closes itself after a few
// seconds, unless the pointer or focus is on it. Warnings and errors stay
// until closed.
//
// A refused save's errors join them: the "Please correct the errors below"
// note, and errors that belong to no one field -- the whole form's, a line's,
// or all the lines' ("Not enough stock: ..."). An error on a single field
// stays beside that field, which a popup could not point at.
const MESSAGE_SECONDS = 5;

function formErrorsAsMessages() {
  const notices = [];
  const note = document.querySelector("#order_form .errornote");
  if (note) {
    notices.push(note.textContent.trim());
    note.remove();
  }
  for (const list of document.querySelectorAll("#order_form ul.errorlist.nonfield, #order_form ul.errorlist.nonform")) {
    for (const item of list.querySelectorAll("li")) {
      notices.push(item.textContent.trim());
    }
    // A line's own errors sit in a table row of their own.
    const row = list.closest("tr.row-form-errors");
    (row ?? list).remove();
  }
  if (!notices.length) {
    return;
  }
  let messages = document.querySelector("ul.messagelist");
  if (!messages) {
    messages = document.createElement("ul");
    messages.className = "messagelist";
    document.body.append(messages);
  }
  for (const text of notices) {
    const item = document.createElement("li");
    item.className = "error";
    item.textContent = text;
    messages.append(item);
  }
}

function closeMessage(message) {
  const list = message.parentElement;
  const remove = () => {
    message.remove();
    if (!list.children.length) {
      list.remove();
    }
  };
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    remove();
  } else {
    message.addEventListener("transitionend", remove, { once: true });
    message.classList.add("is-hiding");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  formErrorsAsMessages();
  const list = document.querySelector("ul.messagelist");
  if (!list) {
    return;
  }
  list.setAttribute("role", "status");
  for (const message of list.querySelectorAll("li")) {
    const close = document.createElement("button");
    close.type = "button";
    close.className = "message-close";
    close.setAttribute("aria-label", "Close message");
    close.textContent = "✕";
    close.addEventListener("click", () => closeMessage(message));
    message.append(close);

    if (message.matches(".success, .info")) {
      let timer = setTimeout(() => closeMessage(message), MESSAGE_SECONDS * 1000);
      const hold = () => clearTimeout(timer);
      const resume = () => {
        clearTimeout(timer);
        if (!message.matches(":hover, :focus-within")) {
          timer = setTimeout(() => closeMessage(message), MESSAGE_SECONDS * 1000);
        }
      };
      message.addEventListener("mouseenter", hold);
      message.addEventListener("focusin", hold);
      message.addEventListener("mouseleave", resume);
      message.addEventListener("focusout", resume);
    }
  }
});

document.addEventListener("DOMContentLoaded", () => {
  let top = null;
  try {
    top = sessionStorage.getItem(SCROLL_KEY);
    sessionStorage.removeItem(SCROLL_KEY);
  } catch {
    return;
  }
  const lines = document.getElementById("items-group");
  if (top !== null && lines) {
    window.scrollTo(0, window.scrollY + lines.getBoundingClientRect().top - Number(top));
  }
});

function addDialog() {
  return document.getElementById("items-add-dialog");
}

function openAddDialog() {
  const candy = document.getElementById("items-add-candy");
  if (!candy.options.length) {
    // The same choices as a new row's dropdown, from Django's row template.
    for (const option of document.querySelectorAll('#items-empty select[name$="-candy"] option')) {
      candy.add(option.cloneNode(true));
    }
  }
  candy.value = "";
  document.getElementById("items-add-quantity").value = "1";
  addDialog().showModal();
  candy.focus();
}

function addLine() {
  const candy = document.getElementById("items-add-candy");
  const quantity = document.getElementById("items-add-quantity");
  if (!candy.reportValidity() || !quantity.reportValidity()) {
    return;
  }
  addDialog().close();
  // The line goes in as the formset's next form, as a row added in the page
  // would; its unit price is left out, so the server uses the candy's price.
  const form = addDialog().closest("form");
  const total = document.getElementById("id_items-TOTAL_FORMS");
  const index = Number(total.value);
  for (const [field, value] of [["candy", candy.value], ["quantity", quantity.value]]) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = `items-${index}-${field}`;
    input.value = value;
    form.append(input);
  }
  total.value = index + 1;
  saveOrder();
}

// The dialog sits inside the admin's form: Enter in its quantity would
// otherwise submit the whole order.
document.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && event.target.matches("#items-add-dialog input")) {
    event.preventDefault();
    addLine();
  }
});

// Where the current press began. A click lands on the nearest element holding
// both press and release, so selecting the quantity by dragging and letting go
// outside "clicks" the dialog itself -- which is not a click on the backdrop.
let pressedOn = null;
document.addEventListener("pointerdown", (event) => {
  pressedOn = event.target;
});

document.addEventListener("click", (event) => {
  const opener = event.target.closest("[data-candy-dialog]");
  if (opener) {
    document.getElementById(opener.dataset.candyDialog).showModal();
    return;
  }
  if (event.target.closest("[data-add-line]")) {
    addLine();
    return;
  }
  if (event.target.closest("[data-confirm-remove]")) {
    confirmRemove();
    return;
  }
  const closer = event.target.closest("[data-close-dialog]");
  if (closer) {
    closer.closest("dialog").close();
    return;
  }
  // A dialog's content fills it, so a press and release both on the dialog
  // itself were on the backdrop around it.
  if (event.target instanceof HTMLDialogElement && pressedOn === event.target) {
    event.target.close();
  }
});
