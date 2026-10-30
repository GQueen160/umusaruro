(function () {
  "use strict";

  const open = document.getElementById("chat-open");
  const panel = document.getElementById("chat-panel");
  const log = document.getElementById("chat-log");
  const form = document.getElementById("chat-form");
  const box = document.getElementById("chat-q");
  const close = document.getElementById("chat-close");
  const token = document.querySelector('meta[name="csrf-token"]');
  if (!open || !panel || !form || !box || !token) return;

  function add(who, text, aside) {
    const line = document.createElement("p");
    line.className = "chat-line " + who + (aside ? " aside" : "");
    const label = document.createElement("b");
    label.textContent = who === "you" ? form.dataset.you : form.dataset.us;
    line.appendChild(label);
    line.appendChild(document.createTextNode(text));
    log.appendChild(line);
    line.scrollIntoView({ block: "nearest" });
    return line;
  }

  open.addEventListener("click", function () {
    panel.hidden = false;
    open.hidden = true;
    box.focus();
  });
  close.addEventListener("click", function () {
    panel.hidden = true;
    open.hidden = false;
    open.focus();
  });
  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape" || panel.hidden) return;
    panel.hidden = true;
    open.hidden = false;
  });
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    const message = box.value.trim();
    if (!message || form.dataset.busy === "1") return;
    box.value = "";
    add("you", message, false);
    form.dataset.busy = "1";
    const wait = document.createElement("p");
    wait.className = "chat-line us wait";
    wait.textContent = form.dataset.wait;
    log.appendChild(wait);
    const page = window.umusaruroContext ? window.umusaruroContext() : {};
    fetch("/api/chat/", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": token.content },
      body: JSON.stringify({
        message: message,
        place: page && page.place ? page.place : null,
        crops: page && page.crops ? page.crops : [],
      }),
    }).then(function (response) {
      return response.json().then(function (data) {
        data.ok = response.ok;
        return data;
      });
    }).then(function (data) {
      wait.remove();
      add("us", data.answer || form.dataset.fail, data.about === false && data.ready !== false);
    }).catch(function () {
      wait.remove();
      add("us", form.dataset.fail, false);
    }).then(function () {
      form.dataset.busy = "";
      box.focus();
    });
  });
})();
