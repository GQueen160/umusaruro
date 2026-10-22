// Map layers and the district side panel. Without this script every district
// still links to its full sheet and the map shows the action layer.
(function () {
  "use strict";

  const block = document.querySelector(".map-block");
  if (!block) return;

  const switcher = block.querySelector(".layers");
  const panel = document.getElementById("panel");
  const body = panel.querySelector(".panel-body");
  const regions = Array.from(block.querySelectorAll("a.region"));
  const layerKeys = Array.from(switcher.querySelectorAll("button")).map((b) => b.dataset.layer);
  let opener = null;
  let request = 0;

  function setParam(key, value) {
    const url = new URL(window.location.href);
    if (value) url.searchParams.set(key, value);
    else url.searchParams.delete(key);
    window.history.replaceState(null, "", url);
  }

  function setLayer(key) {
    if (!layerKeys.includes(key)) return;
    block.dataset.layer = key;
    switcher.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.layer === key)));
    block.querySelectorAll(".legend-layer").forEach((l) => { l.hidden = l.dataset.layer !== key; });
    setParam("layer", key === layerKeys[0] ? "" : key);
  }

  function select(slug) {
    regions.forEach((r) => r.classList.toggle("selected", r.dataset.slug === slug));
  }

  async function open(region) {
    const mine = ++request;
    opener = region;
    select(region.dataset.slug);
    panel.classList.add("open");
    panel.removeAttribute("inert");
    panel.setAttribute("aria-hidden", "false");
    body.innerHTML = '<p class="loading">Loading the district sheet…</p>';
    setParam("d", region.dataset.slug);
    try {
      const response = await fetch(region.dataset.panel, { headers: { "X-Requested-With": "fetch" } });
      if (!response.ok) throw new Error(response.statusText);
      const html = await response.text();
      if (mine !== request) return;
      body.innerHTML = html;
      body.scrollTop = 0;
      body.focus({ preventScroll: true });
    } catch (error) {
      window.location.href = region.href;
    }
  }

  function close() {
    request++;
    panel.classList.remove("open");
    panel.setAttribute("inert", "");
    panel.setAttribute("aria-hidden", "true");
    select(null);
    setParam("d", "");
    if (opener) opener.focus({ preventScroll: true });
    opener = null;
  }

  switcher.hidden = false;
  switcher.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-layer]");
    if (button) setLayer(button.dataset.layer);
  });

  regions.forEach((region) => {
    region.addEventListener("click", (event) => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return;
      event.preventDefault();
      open(region);
    });
  });

  panel.querySelector(".panel-close").addEventListener("click", close);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && panel.classList.contains("open")) close();
  });

  const params = new URL(window.location.href).searchParams;
  if (params.get("layer")) setLayer(params.get("layer"));
  const start = regions.find((r) => r.dataset.slug === params.get("d"));
  if (start) open(start);
})();
