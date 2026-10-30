(function () {
  "use strict";

  const crops = JSON.parse(document.getElementById("crop-data").textContent);
  const ui = JSON.parse(document.getElementById("ui-copy").textContent);
  const lang = document.body.dataset.lang || "en";
  const token = document.querySelector('meta[name="csrf-token"]').content;
  const state = {
    place: null,
    crops: [],
    advice: null,
    request: 0,
    holding: { unit: "ha", farm: "", portions: {}, note: "" },
    plans: [],
    calendarPlan: null,
    calendarDay: null,
  };
  const pin = L.divIcon({ className: "", html: '<div class="pin"></div>', iconSize: [22, 22] });
  let marker = null;
  let outlines = null;

  const map = L.map("map", { zoomControl: false }).setView([-1.95, 29.9], 8);
  L.control.zoom({ position: "bottomright" }).addTo(map);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    // The page sends Referrer-Policy: same-origin, so a tile request would
    // leave with no Referer. OpenStreetMap then returns its blocked tile.
    referrerPolicy: "origin",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map);

  const els = {
    q: document.getElementById("q"),
    results: document.getElementById("results"),
    prompt: document.getElementById("prompt"),
    place: document.getElementById("place"),
    talk: document.getElementById("talk"),
    crops: document.getElementById("crops"),
    advice: document.getElementById("advice"),
    target: document.getElementById("target"),
    plans: document.getElementById("plans"),
    calendar: document.getElementById("calendar"),
    voice: document.getElementById("voice"),
    flag: document.getElementById("flag"),
    steps: document.getElementById("steps"),
    go: document.getElementById("continue"),
  };

  function post(url, body) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": token },
      body: JSON.stringify(body),
    }).then(function (response) { return response.json().then(function (data) { data.ok = response.ok; return data; }); });
  }

  function bubble(who, text) {
    const node = document.createElement("p");
    node.className = "bubble " + who;
    const label = document.createElement("b");
    label.textContent = who === "you" ? ui.you : ui.us;
    node.appendChild(label);
    node.appendChild(document.createTextNode(text));
    els.talk.appendChild(node);
    node.scrollIntoView({ block: "nearest" });
  }

  function fly(place, zoom) {
    if (place.lat == null || place.lon == null) return;
    map.flyTo([place.lat, place.lon], zoom, { duration: 0.8 });
    if (!marker) marker = L.marker([place.lat, place.lon], { icon: pin }).addTo(map);
    else marker.setLatLng([place.lat, place.lon]);
    if (outlines) {
      outlines.eachLayer(function (layer) {
        const on = layer.feature.properties.district === place.district;
        layer.setStyle({ weight: on ? 3 : 1, color: on ? "#9b2226" : "#1b4332", fillOpacity: on ? 0.08 : 0.02 });
      });
    }
  }

  function lockedOffice() {
    const node = document.getElementById("office-data");
    if (!node) return null;
    try { return JSON.parse(node.textContent); } catch (error) { return null; }
  }

  function showPlace(place) {
    const lock = lockedOffice();
    if (lock) {
      if (place.district && place.district !== lock.district) return;
      if (lock.sector && place.sector && place.sector !== lock.sector) return;
    }
    state.place = place;
    els.prompt.hidden = true;
    els.place.hidden = false;
    els.place.textContent = "";
    const line = [place.village, place.cell, place.sector, place.district].filter(Boolean).join(" · ");
    const strong = document.createElement("span");
    strong.textContent = line || place.district;
    els.place.appendChild(strong);
    if (!place.village_id && document.body.dataset.reader !== "sector") {
      const small = document.createElement("small");
      small.textContent = ui.tap_village;
      els.place.appendChild(small);
    }
    if (document.body.dataset.reader === "sector" && place.district) {
      const link = document.createElement("a");
      link.href = "/district/" + encodeURIComponent(place.district.toLowerCase()) + "/";
      link.textContent = ui.open_district.replace("{name}", place.district);
      const small = document.createElement("small");
      small.appendChild(link);
      els.place.appendChild(small);
    }
    fly(place, place.village_id ? 15 : 11);
    syncJourney();
    if (readerId() === "sector") {
      if (place.sector && place.district) loadAdvice();
      else els.advice.textContent = "";
      return;
    }
    if (state.crops.length) loadAdvice();
  }

  function readerId() {
    return document.body.dataset.reader || "";
  }

  function isDomestic() {
    return readerId() === "farmer-domestic";
  }

  function isHolding() {
    return readerId() === "farmer-mini" || readerId() === "farmer-large";
  }

  function isFarmer() {
    return isDomestic() || isHolding();
  }

  function hasVillage() {
    return !!(state.place && state.place.village_id);
  }

  function syncJourney() {
    if (!isFarmer()) {
      els.crops.hidden = false;
      return;
    }
    const village = hasVillage();
    els.crops.hidden = !village;
    if (els.flag) els.flag.hidden = !village;
    if (village && !state.crops.length) {
      els.prompt.hidden = false;
      els.prompt.textContent = ui.prompt_crops;
    }
    if (!els.steps) return;
    const step = !village ? "place" : (state.crops.length ? "ask" : "crops");
    els.steps.querySelectorAll("li").forEach(function (item) {
      if (item.dataset.step === step) item.setAttribute("aria-current", "step");
      else item.removeAttribute("aria-current");
    });
    if (els.go) els.go.hidden = !village || !state.crops.length;
  }

  function loadAdvice() {
    if (!state.place || !state.place.district) return;
    if (readerId() !== "sector" && !state.crops.length) return;
    const mine = ++state.request;
    const body = { district: state.place.district, crops: state.crops, reader: readerId() };
    post("/api/advice/", body).then(function (data) {
      if (mine !== state.request || !data.advice) return;
      state.advice = data.advice;
      renderAdvice(data.advice);
    });
  }

  function paintFlag(kind) {
    document.querySelectorAll(".flag-item").forEach(function (item) {
      if (item.dataset.flag === kind) item.setAttribute("aria-current", "true");
      else item.removeAttribute("aria-current");
    });
    const line = document.getElementById("flag-line");
    if (!line) return;
    const key = kind ? "flag_" + kind + "_line" : "flag_wait";
    line.textContent = ui[key] || "";
  }

  function renderAdvice(advice) {
    paintFlag(advice.flag);
    syncJourney();
    if (isDomestic()) {
      els.advice.textContent = "";
      renderTarget(null);
      return;
    }
    if (isHolding()) {
      renderHolding();
      return;
    }
    if (readerId() === "sector" && advice.board) {
      renderSector(advice);
      return;
    }
    renderCards(advice);
  }

  function renderSector(advice) {
    els.advice.textContent = "";
    const board = advice.board;
    const note = document.createElement("p");
    note.className = "note";
    note.textContent = advice["note_" + lang] || advice.note_en;
    const head = document.createElement("h2");
    head.className = "board-action " + board.action;
    head.textContent = board["title_" + lang] || board.title_en;
    els.advice.appendChild(note);
    els.advice.appendChild(head);
    let crops = false;
    board.rows.forEach(function (row) {
      if (row.unit === "kg/ha") crops = true;
      const block = document.createElement("section");
      block.className = "board-row";
      const title = document.createElement("h3");
      title.textContent = row["title_" + lang] || row.title_en;
      block.appendChild(title);
      row.bars.forEach(function (bar) {
        const line = document.createElement("div");
        line.className = "board-line";
        const name = document.createElement("span");
        name.textContent = bar["label_" + lang] || bar.label_en;
        const track = document.createElement("div");
        track.className = "board-track";
        if (!bar.blank && bar.width) {
          const fill = document.createElement("span");
          fill.className = "board-fill " + bar.key;
          fill.style.width = bar.width + "%";
          track.appendChild(fill);
        }
        const value = document.createElement("span");
        value.className = "board-value";
        if (bar.blank) {
          value.textContent = ui.board_blank;
        } else {
          const num = document.createElement("b");
          num.textContent = bar.value + " " + bar.unit;
          value.appendChild(num);
          if (bar.url) {
            const link = document.createElement("a");
            link.href = bar.url;
            link.target = "_blank";
            link.rel = "noopener";
            link.textContent = bar.survey + " · " + bar.table;
            value.appendChild(link);
          }
        }
        line.appendChild(name);
        line.appendChild(track);
        line.appendChild(value);
        block.appendChild(line);
      });
      const caption = document.createElement("p");
      caption.className = "board-caption";
      caption.textContent = row["caption_" + lang] || row.caption_en;
      block.appendChild(caption);
      els.advice.appendChild(block);
    });
    if (!crops) {
      const hint = document.createElement("p");
      hint.className = "board-caption";
      hint.textContent = ui.board_pick;
      els.advice.appendChild(hint);
    }
  }

  function renderDomestic(advice) {
    els.advice.textContent = "";
    const block = document.createElement("section");
    block.className = "card holding";
    (advice.domestic && advice.domestic.lines || []).forEach(function (line) {
      const p = document.createElement("p");
      p.textContent = line[lang] || line.en;
      block.appendChild(p);
    });
    els.advice.appendChild(block);
    renderTarget(null);
  }

  function rateFor(crop) {
    const rates = (state.advice && state.advice.rates) || [];
    return rates.filter(function (row) { return row.crop === crop; })[0] || null;
  }

  function amount(value) {
    const size = Number(String(value || "").replace(",", "."));
    if (!isFinite(size) || size <= 0) return 0;
    return size;
  }

  function numericText(value) {
    const text = String(value || "");
    let out = "";
    let sep = false;
    let dropped = false;
    for (let i = 0; i < text.length; i++) {
      const ch = text[i];
      if (ch >= "0" && ch <= "9") out += ch;
      else if ((ch === "." || ch === ",") && !sep) {
        sep = true;
        out += ch;
      } else dropped = true;
    }
    return { text: out, dropped: dropped };
  }

  function bindNumber(input, note, apply) {
    let held = false;
    function show(on) {
      input.classList.toggle("digits", on);
      note.hidden = !on;
      note.textContent = on ? ui.digits_only : "";
      if (on) input.setAttribute("aria-invalid", "true");
      else if (!input.classList.contains("bad")) input.removeAttribute("aria-invalid");
    }
    function write(value, caret) {
      if (input.value !== value) {
        input.value = value;
        if (caret != null && input.setSelectionRange) {
          const at = Math.max(0, Math.min(caret, value.length));
          input.setSelectionRange(at, at);
        }
      }
      apply(value);
    }
    input.autocomplete = "off";
    input.spellcheck = false;
    input.addEventListener("beforeinput", function (event) {
      const kind = event.inputType || "";
      if (kind.indexOf("insert") !== 0 || event.data == null) return;
      const start = input.selectionStart == null ? input.value.length : input.selectionStart;
      const end = input.selectionEnd == null ? start : input.selectionEnd;
      const raw = input.value.slice(0, start) + event.data + input.value.slice(end);
      const next = numericText(raw);
      if (!next.dropped) {
        held = false;
        return;
      }
      event.preventDefault();
      held = true;
      write(next.text, start + numericText(event.data).text.length);
      show(true);
    });
    input.addEventListener("input", function () {
      const next = numericText(input.value);
      if (next.dropped) {
        held = false;
        write(next.text, input.selectionStart);
        show(true);
        return;
      }
      if (held) {
        held = false;
        apply(input.value);
        return;
      }
      show(false);
      apply(input.value);
    });
  }

  function digitsNote() {
    const note = document.createElement("p");
    note.className = "digits-note";
    note.hidden = true;
    return note;
  }

  function trimNum(value) {
    const n = Math.round(Number(value) * 10000) / 10000;
    return String(n);
  }

  function unitWord() {
    return state.holding.unit === "m2" ? ui.unit_m2 : ui.unit_ha;
  }

  function fill(template, values) {
    return String(template || "").replace(/\{(\w+)\}/g, function (_, key) {
      return values[key] == null ? "" : values[key];
    });
  }

  function cropName(id) {
    const rate = rateFor(id);
    if (rate) return rate[lang] || rate.en;
    const crop = crops.filter(function (item) { return item.id === id; })[0];
    return crop ? (crop[lang] || crop.en) : id;
  }

  function landUse() {
    const unit = unitWord();
    const lines = [];
    let used = 0;
    state.crops.forEach(function (id) {
      const row = state.holding.portions[id] || {};
      const area = amount(row.area);
      if (!area) return;
      used += area;
      lines.push(cropName(id) + ": " + trimNum(area) + " " + unit);
    });
    return { unit: unit, used: used, lines: lines, farm: amount(state.holding.farm) };
  }

  function measureText() {
    const land = landUse();
    if (!land.lines.length || !land.farm) return "";
    const values = {
      used: trimNum(land.used),
      farm: trimNum(land.farm),
      over: trimNum(land.used - land.farm),
      left: trimNum(land.farm - land.used),
      unit: land.unit,
    };
    if (land.used > land.farm + 1e-9) {
      const together = land.lines.length > 1 ? " " + fill(ui.together, values) : "";
      return ui.exceed_farm + " " + land.lines.join(". ") + "." + together + " " + fill(ui.over_farm, values);
    }
    if (land.farm - land.used <= 1e-9) return "";
    return land.lines.join(". ") + ". " + fill(ui.fit_farm, values);
  }

  function portionsOverFarm() {
    const land = landUse();
    return land.farm > 0 && land.used > land.farm + 1e-9;
  }

  function toHa(amountValue, unit) {
    const size = amount(amountValue);
    if (!size) return 0;
    return unit === "m2" ? size / 10000 : size;
  }

  function portionKg(kgPerHa, amountValue, unit) {
    const rate = Number(kgPerHa);
    const ha = toHa(amountValue, unit);
    if (!rate || !ha) return "";
    return String(Math.round(ha * rate));
  }

  function group(value) {
    return String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  function convertAmount(value, from, to) {
    if (from === to) return value;
    const n = amount(value);
    if (!n) return value;
    const ha = from === "m2" ? n / 10000 : n;
    return trimNum(to === "m2" ? ha * 10000 : ha);
  }

  function blameId() {
    const farm = amount(state.holding.farm);
    if (!farm) return "";
    let used = 0;
    let blame = "";
    state.crops.forEach(function (id) {
      const area = amount((state.holding.portions[id] || {}).area);
      if (!area) return;
      if (!blame && used + area > farm + 1e-9) blame = id;
      used += area;
    });
    return blame;
  }

  function countryLine(rate, amountValue) {
    if (!rate || !rate.kg_ha) return ui.no_country;
    if (portionsOverFarm()) return "";
    const name = rate.kind === "goal" ? ui.country_goal : ui.country_harvest;
    let text = name + ": " + rate.shown + " " + ui.per_ha;
    const area = amount(amountValue);
    const kg = portionKg(rate.kg_ha, area, state.holding.unit);
    if (kg && area) text += ", " + fill(ui.on_land, { kg: group(kg) });
    else text += ".";
    return text;
  }

  function renderHolding() {
    els.advice.textContent = "";
    if (!state.holding.farm && !state.crops.some(function (id) {
      const row = state.holding.portions[id] || {};
      return row.area || row.target;
    })) {
      renderTarget(null);
      return;
    }
    const block = document.createElement("section");
    block.className = "card holding";
    const heading = document.createElement("h2");
    heading.textContent = ui.summary_title;
    block.appendChild(heading);
    const size = document.createElement("p");
    size.textContent = ui.farm_size + " " + state.holding.farm + " " + unitWord();
    block.appendChild(size);
    state.crops.forEach(function (id) {
      const rate = rateFor(id);
      const row = state.holding.portions[id] || {};
      const title = document.createElement("h2");
      title.textContent = cropName(id);
      const portion = document.createElement("p");
      portion.textContent = fill(ui.portion_for, { name: title.textContent, unit: unitWord() }) + (row.area ? " " + trimNum(amount(row.area)) + " " + unitWord() : "");
      block.appendChild(title);
      block.appendChild(portion);
      if (row.target) {
        const target = document.createElement("p");
        target.textContent = ui.your_target + " " + row.target;
        block.appendChild(target);
      }
      const line = countryLine(rate, row.area);
      if (line) {
        const country = document.createElement("p");
        country.className = "country";
        country.textContent = line;
        block.appendChild(country);
      }
    });
    const measured = measureText();
    if (measured) {
      const over = document.createElement("p");
      over.className = portionsOverFarm() ? "measure over" : "measure";
      over.textContent = measured;
      block.appendChild(over);
    }
    const change = document.createElement("button");
    change.type = "button";
    change.className = "change";
    change.textContent = ui.change_farm;
    change.addEventListener("click", openPopup);
    block.appendChild(change);
    els.advice.appendChild(block);
    renderTarget(null);
  }

  function popupNode() {
    let node = document.getElementById("popup");
    if (node) return node;
    node = document.createElement("div");
    node.id = "popup";
    node.className = "popup";
    node.hidden = true;
    node.addEventListener("click", function (event) {
      if (event.target === node) closePopup(true);
    });
    document.body.appendChild(node);
    return node;
  }

  function closePopup(keep) {
    const node = document.getElementById("popup");
    if (!node) return;
    const wasOpen = !node.hidden;
    node.hidden = true;
    node.innerHTML = "";
    node.removeAttribute("role");
    if (keep && wasOpen && isDomestic() && state.advice) renderDomestic(state.advice);
  }

  function openPopup() {
    if (!isFarmer() || !hasVillage() || !state.crops.length || !state.advice) return;
    const node = popupNode();
    node.hidden = false;
    node.setAttribute("role", "dialog");
    node.setAttribute("aria-modal", "true");
    node.innerHTML = "";
    const card = document.createElement("div");
    card.className = "popup-card";
    const title = document.createElement("h2");
    title.id = "popup-title";
    title.textContent = isDomestic() ? ui.popup_garden : ui.popup_farm;
    const where = document.createElement("p");
    where.className = "where";
    const names = state.crops.map(function (id) {
      const crop = crops.filter(function (item) { return item.id === id; })[0];
      return crop ? (crop[lang] || crop.en) : id;
    });
    where.textContent = [state.place.village, state.place.district].filter(Boolean).join(" · ") + " · " + names.join(", ");
    card.appendChild(title);
    card.appendChild(where);
    node.setAttribute("aria-labelledby", "popup-title");
    if (isDomestic()) fillDomestic(card);
    else fillHolding(card);
    node.appendChild(card);
    const focus = card.querySelector("input, button");
    if (focus) focus.focus();
  }

  function fillDomestic(card) {
    const lines = (state.advice.domestic && state.advice.domestic.lines) || [];
    lines.forEach(function (line) {
      const p = document.createElement("p");
      p.textContent = line[lang] || line.en;
      card.appendChild(p);
    });
    const close = document.createElement("button");
    close.type = "button";
    close.className = "done";
    close.textContent = ui.popup_close;
    close.addEventListener("click", function () { closePopup(true); });
    card.appendChild(close);
  }

  function fieldRow(input, aside) {
    const row = document.createElement("div");
    row.className = "field-row";
    row.appendChild(input);
    row.appendChild(aside);
    return row;
  }

  function unitWordSpan() {
    const unit = document.createElement("span");
    unit.className = "unit-word";
    unit.textContent = unitWord();
    return unit;
  }

  function unitSwitch() {
    const wrap = document.createElement("span");
    wrap.className = "unit-pick";
    [["ha", ui.unit_ha], ["m2", ui.unit_m2]].forEach(function (item) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = item[1];
      if (state.holding.unit === item[0]) button.setAttribute("aria-pressed", "true");
      button.addEventListener("click", function () {
        const previous = state.holding.unit;
        if (previous === item[0]) return;
        state.holding.unit = item[0];
        state.holding.farm = convertAmount(state.holding.farm, previous, state.holding.unit);
        state.crops.forEach(function (id) {
          const row = state.holding.portions[id];
          if (row) row.area = convertAmount(row.area, previous, state.holding.unit);
        });
        openPopup();
      });
      wrap.appendChild(button);
    });
    return wrap;
  }

  function fillHolding(card) {
    const sizeLabel = document.createElement("label");
    sizeLabel.textContent = ui.farm_size;
    const size = document.createElement("input");
    size.inputMode = "decimal";
    size.value = state.holding.farm;
    const sizeNote = digitsNote();
    bindNumber(size, sizeNote, function (value) {
      state.holding.farm = value;
      paintCountry();
    });
    sizeLabel.className = "ask";
    sizeLabel.appendChild(fieldRow(size, unitSwitch()));
    card.appendChild(sizeLabel);
    card.appendChild(sizeNote);
    const room = document.createElement("p");
    room.className = "measure";
    room.hidden = true;
    state.crops.forEach(function (id) {
      const rate = rateFor(id);
      const name = cropName(id);
      if (!state.holding.portions[id]) state.holding.portions[id] = { area: "", target: "" };
      const row = state.holding.portions[id];
      const portionLabel = document.createElement("label");
      portionLabel.className = "ask";
      portionLabel.dataset.ask = "scale-" + id;
      portionLabel.textContent = fill(ui.portion_for, { name: name, unit: unitWord() });
      const portion = document.createElement("input");
      portion.inputMode = "decimal";
      portion.value = row.area;
      portion.dataset.area = id;
      const portionNote = digitsNote();
      bindNumber(portion, portionNote, function (value) {
        row.area = value;
        paintCountry();
      });
      portionLabel.appendChild(fieldRow(portion, unitWordSpan()));
      const flag = document.createElement("p");
      flag.className = "measure over";
      flag.dataset.flag = id;
      flag.hidden = true;
      card.appendChild(portionLabel);
      card.appendChild(portionNote);
      card.appendChild(flag);
      const targetLabel = document.createElement("label");
      targetLabel.className = "ask";
      targetLabel.dataset.ask = "goal-" + id;
      targetLabel.textContent = ui.your_target;
      const target = document.createElement("input");
      target.inputMode = "decimal";
      target.value = row.target;
      const targetNote = digitsNote();
      bindNumber(target, targetNote, function (value) {
        row.target = value;
        paintCountry();
      });
      targetLabel.appendChild(target);
      card.appendChild(targetLabel);
      card.appendChild(targetNote);
      const country = document.createElement("p");
      country.className = "country";
      country.dataset.crop = id;
      country.textContent = countryLine(rate, row.area);
      card.appendChild(country);
    });
    card.appendChild(room);
    function paintFocus() {
      const farmReady = amount(state.holding.farm) > 0;
      const over = portionsOverFarm();
      const blame = blameId();
      sizeLabel.className = "ask " + (farmReady ? "answered" : "now");
      if (farmReady && !over) sizeLabel.removeAttribute("aria-current");
      else if (!farmReady) sizeLabel.setAttribute("aria-current", "step");
      else sizeLabel.removeAttribute("aria-current");
      let open = !farmReady;
      state.crops.forEach(function (id) {
        const scale = card.querySelector('[data-ask="scale-' + id + '"]');
        const goal = card.querySelector('[data-ask="goal-' + id + '"]');
        const row = state.holding.portions[id] || {};
        const areaReady = amount(row.area) > 0;
        const goalReady = amount(row.target) > 0;
        let scaleState = "wait";
        let goalState = "wait";
        if (!farmReady) {
          scaleState = "wait";
          goalState = "wait";
        } else if (over && id === blame) {
          scaleState = "now";
          open = true;
        } else if (over) {
          scaleState = areaReady ? "answered" : "wait";
        } else if (open) {
          scaleState = "wait";
        } else if (!areaReady) {
          scaleState = "now";
          open = true;
        } else if (!goalReady) {
          scaleState = "answered";
          goalState = "now";
          open = true;
        } else {
          scaleState = "answered";
          goalState = "answered";
        }
        scale.className = "ask " + scaleState;
        goal.className = "ask " + goalState;
        if (scaleState === "now") scale.setAttribute("aria-current", "step");
        else scale.removeAttribute("aria-current");
        if (goalState === "now") goal.setAttribute("aria-current", "step");
        else goal.removeAttribute("aria-current");
      });
    }
    function paintCountry() {
      const over = portionsOverFarm();
      const blame = blameId();
      card.querySelectorAll("input[data-area]").forEach(function (input) {
        const bad = over && amount(input.value) > 0;
        input.classList.toggle("bad", bad);
        if (bad || input.classList.contains("digits")) input.setAttribute("aria-invalid", "true");
        else input.removeAttribute("aria-invalid");
      });
      paintFocus();
      card.querySelectorAll(".country").forEach(function (node) {
        const rate = rateFor(node.dataset.crop);
        const row = state.holding.portions[node.dataset.crop] || {};
        const text = countryLine(rate, row.area);
        const goal = card.querySelector('[data-ask="goal-' + node.dataset.crop + '"]');
        const show = text && goal && !goal.classList.contains("wait");
        node.hidden = !show;
        node.textContent = text;
      });
      card.querySelectorAll("[data-flag]").forEach(function (node) {
        const show = over && node.dataset.flag === blame;
        node.hidden = !show;
        node.textContent = show ? measureText() : "";
      });
      const fit = over ? "" : measureText();
      room.hidden = !fit;
      room.textContent = fit;
    }
    paintCountry();
    const done = document.createElement("button");
    done.type = "button";
    done.className = "done";
    done.textContent = ui.popup_done;
    done.addEventListener("click", function () {
      if (portionsOverFarm()) {
        paintCountry();
        return;
      }
      closePopup();
      renderHolding();
      openRoutine();
    });
    card.appendChild(done);
  }

  function openRoutine() {
    const node = popupNode();
    node.hidden = false;
    node.setAttribute("role", "dialog");
    node.setAttribute("aria-modal", "true");
    node.innerHTML = "";
    const card = document.createElement("div");
    card.className = "popup-card plan-card";
    const title = document.createElement("h2");
    title.id = "popup-title";
    title.textContent = ui.plan_title;
    card.appendChild(title);
    node.setAttribute("aria-labelledby", "popup-title");
    node.appendChild(card);
    post("/api/routine/", {
      district: state.place.district,
      crops: state.crops,
      unit: state.holding.unit,
      farm: state.holding.farm,
      portions: state.holding.portions,
    }).then(function (data) {
      if (!data.ok || !data.routine) return;
      const routine = data.routine;
      function lines(items, className) {
        (items || []).forEach(function (line) {
          const p = document.createElement("p");
          p.className = className;
          p.textContent = line[lang] || line.en;
          card.appendChild(p);
        });
      }
      lines(routine.summary, "summary-line");
      const daily = document.createElement("h3");
      daily.textContent = ui.plan_daily;
      card.appendChild(daily);
      lines(routine.daily, "daily");
      const weekly = document.createElement("h3");
      weekly.className = "weekly-title";
      weekly.textContent = ui.plan_weekly;
      card.appendChild(weekly);
      lines(routine.weekly, "weekly");
      const save = document.createElement("button");
      save.type = "button";
      save.className = "done";
      save.textContent = ui.save_plan;
      save.addEventListener("click", function () {
        const portions = state.holding.portions;
        let targetCrop = state.crops[0];
        let targetKg = "";
        state.crops.forEach(function (id) {
          const row = portions[id] || {};
          if (!targetKg && amount(row.target)) {
            targetCrop = id;
            targetKg = row.target;
          }
        });
        save.disabled = true;
        post("/api/plans/save/", {
          village_id: state.place.village_id,
          crops: state.crops,
          target_crop: targetCrop,
          target_kg: targetKg,
          unit: state.holding.unit,
          farm: state.holding.farm,
          portions: portions,
        }).then(function (data) {
          if (!data.ok) {
            save.disabled = false;
            bubble("us", data.error || ui.failed);
            return;
          }
          bubble("us", ui.plan_saved);
          state.calendarPlan = data.plan.id;
          state.calendarDay = data.plan.journey ? data.plan.journey.today : null;
          loadPlans(true);
          closePopup();
        });
      });
      card.appendChild(save);
    });
  }

  function renderCards(advice) {
    els.advice.textContent = "";
    const note = document.createElement("p");
    note.className = "note";
    note.textContent = advice["note_" + lang] || advice.note_en;
    els.advice.appendChild(note);
    advice.cards.forEach(function (card) {
      const box = document.createElement("article");
      box.className = "card " + card.kind;
      const title = document.createElement("h2");
      title.textContent = card["title_" + lang] || card.title_en;
      const body = document.createElement("p");
      body.textContent = card["body_" + lang] || card.body_en;
      box.appendChild(title);
      box.appendChild(body);
      if (card.facts && card.facts.length) {
        const facts = document.createElement("div");
        facts.className = "facts";
        card.facts.forEach(function (fact) {
          const item = document.createElement("div");
          item.className = "fact";
          const value = document.createElement("b");
          value.textContent = fact.value + " " + fact.unit;
          const link = document.createElement("a");
          link.href = fact.url;
          link.target = "_blank";
          link.rel = "noopener";
          link.textContent = fact.survey + " " + fact.table;
          item.appendChild(value);
          const labels = fact.labels || {};
          item.appendChild(document.createTextNode(" " + (labels[lang] || fact.label)));
          item.appendChild(document.createElement("br"));
          item.appendChild(link);
          facts.appendChild(item);
        });
        box.appendChild(facts);
      }
      els.advice.appendChild(box);
    });
    renderTarget(advice.target);
  }

  function renderTarget(target) {
    if (!els.target) return;
    els.target.textContent = "";
    if (!target) {
      els.target.hidden = true;
      return;
    }
    els.target.hidden = false;
    const title = document.createElement("h2");
    const names = {en: target.en, fr: target.fr, rw: target.rw};
    const whys = {en: target.why_en, fr: target.why_fr, rw: target.why_rw};
    title.textContent = (names[lang] || target.en);
    const why = document.createElement("p");
    why.textContent = whys[lang] || target.why_en;
    const row = document.createElement("div");
    row.className = "stepper";
    const down = document.createElement("button");
    down.type = "button";
    down.textContent = "−";
    const input = document.createElement("input");
    input.id = "kg";
    input.inputMode = "decimal";
    input.value = String(Math.round(Number(target.kg)));
    const up = document.createElement("button");
    up.type = "button";
    up.textContent = "+";
    const kgNote = digitsNote();
    bindNumber(input, kgNote, function () {});
    down.addEventListener("click", function () {
      input.value = String(Math.max(100, Number(input.value) - 100));
      input.dispatchEvent(new Event("input", { bubbles: true }));
    });
    up.addEventListener("click", function () {
      input.value = String(Number(input.value) + 100);
      input.dispatchEvent(new Event("input", { bubbles: true }));
    });
    const save = document.createElement("button");
    save.id = "save";
    save.type = "submit";
    save.textContent = ui.save_aim;
    row.appendChild(down);
    row.appendChild(input);
    row.appendChild(up);
    els.target.appendChild(title);
    els.target.appendChild(why);
    els.target.appendChild(row);
    els.target.appendChild(kgNote);
    els.target.appendChild(save);
    els.target.onsubmit = function (event) {
      event.preventDefault();
      if (!state.place || !state.place.village_id) {
        bubble("us", ui.need_village);
        return;
      }
      post("/api/plans/save/", {
        village_id: state.place.village_id,
        crops: state.crops,
        target_crop: target.crop,
        target_kg: input.value,
      }).then(function (data) {
        if (!data.ok) {
          bubble("us", data.error || ui.failed);
          return;
        }
        bubble("us", ui.saved + ": " + data.plan.target_kg + " kg/ha · " + data.plan.village);
        loadPlans();
      });
    };
  }

  function paintCrops() {
    els.crops.textContent = "";
    crops.forEach(function (crop) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "crop" + (state.crops.indexOf(crop.id) >= 0 ? " on" : "");
      button.textContent = crop[lang] || crop.en;
      const en = document.createElement("small");
      en.textContent = lang === "rw" ? crop.en : crop.rw;
      button.appendChild(en);
      button.addEventListener("click", function () {
        const index = state.crops.indexOf(crop.id);
        if (index >= 0) state.crops.splice(index, 1);
        else if (state.crops.length < 4) state.crops.push(crop.id);
        paintCrops();
        syncJourney();
        if (!state.crops.length) {
          els.advice.textContent = "";
          closePopup();
          if (els.target) {
            els.target.hidden = true;
            els.target.textContent = "";
          }
          paintFlag(null);
          return;
        }
        loadAdvice();
      });
      els.crops.appendChild(button);
    });
  }

  function applyHeard(data) {
    bubble("you", data.heard);
    bubble("us", data["reply_" + lang] || data.reply_en);
    state.crops = data.crops || [];
    paintCrops();
    if (data.place) showPlace(data.place);
    if (data.advice) {
      state.advice = data.advice;
      renderAdvice(data.advice);
    }
    if (data.choices && data.choices.length) {
      data.choices.forEach(function (place) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "crop";
        button.textContent = place.village + " · " + place.cell + " · " + place.district;
        button.addEventListener("click", function () { showPlace(place); });
        els.talk.appendChild(button);
      });
    }
  }

  function fillSelect(select, places, label) {
    select.textContent = "";
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = label;
    select.appendChild(blank);
    places.forEach(function (place) {
      const option = document.createElement("option");
      option.value = place.village_id || place.id;
      option.textContent = place.village || place.name;
      option.dataset.place = JSON.stringify(place);
      select.appendChild(option);
    });
    select.disabled = places.length === 0;
  }

  const picks = {
    district: document.getElementById("pick-district"),
    sector: document.getElementById("pick-sector"),
    cell: document.getElementById("pick-cell"),
    village: document.getElementById("pick-village"),
  };

  if (picks.district) {
  fetch("/api/places/").then(function (r) { return r.json(); }).then(function (data) {
    fillSelect(picks.district, data.places, ui.opt_district);
  });

  picks.district.addEventListener("change", function () {
    const option = picks.district.selectedOptions[0];
    fillSelect(picks.sector, [], ui.opt_sector);
    fillSelect(picks.cell, [], ui.opt_cell);
    fillSelect(picks.village, [], ui.opt_village);
    if (!option || !option.dataset.place) return;
    const place = JSON.parse(option.dataset.place);
    showPlace({ district: place.name, lat: place.lat, lon: place.lon, village_id: "" });
    fetch("/api/places/?district=" + encodeURIComponent(place.name)).then(function (r) { return r.json(); }).then(function (data) {
      fillSelect(picks.sector, data.places, ui.opt_sector);
    });
  });

  picks.sector.addEventListener("change", function () {
    const option = picks.sector.selectedOptions[0];
    fillSelect(picks.cell, [], ui.opt_cell);
    fillSelect(picks.village, [], ui.opt_village);
    if (!option || !option.value) return;
    const place = JSON.parse(option.dataset.place);
    showPlace({ district: state.place.district, sector: place.name, sector_id: place.id, lat: place.lat, lon: place.lon, village_id: "" });
    fetch("/api/places/?sector_id=" + encodeURIComponent(place.id)).then(function (r) { return r.json(); }).then(function (data) {
      fillSelect(picks.cell, data.places, ui.opt_cell);
    });
  });

  picks.cell.addEventListener("change", function () {
    const option = picks.cell.selectedOptions[0];
    fillSelect(picks.village, [], ui.opt_village);
    if (!option || !option.value) return;
    const place = JSON.parse(option.dataset.place);
    showPlace({
      district: state.place.district,
      sector: state.place.sector,
      cell: place.name,
      lat: place.lat,
      lon: place.lon,
      village_id: "",
    });
    fetch("/api/places/?cell_id=" + encodeURIComponent(place.id)).then(function (r) { return r.json(); }).then(function (data) {
      fillSelect(picks.village, data.places, ui.opt_village);
    });
  });

  picks.village.addEventListener("change", function () {
    const option = picks.village.selectedOptions[0];
    if (!option || !option.dataset.place) return;
    showPlace(JSON.parse(option.dataset.place));
  });
  }

  const searchForm = document.getElementById("search");
  const sheet = document.getElementById("sheet");
  let searchTimer = 0;
  let searchLeave = 0;

  function beginSearch() {
    clearTimeout(searchLeave);
    document.body.classList.add("searching");
  }

  function endSearch(pop) {
    clearTimeout(searchLeave);
    document.body.classList.remove("searching");
    els.results.hidden = true;
    if (!pop) return;
    sheet.classList.remove("in");
    void sheet.offsetWidth;
    sheet.classList.add("in");
  }

  els.q.addEventListener("focus", beginSearch);
  els.q.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    endSearch(false);
    els.q.blur();
  });
  searchForm.addEventListener("focusout", function () {
    clearTimeout(searchLeave);
    searchLeave = setTimeout(function () {
      if (searchForm.contains(document.activeElement)) return;
      endSearch(false);
    }, 180);
  });

  els.q.addEventListener("input", function () {
    beginSearch();
    clearTimeout(searchTimer);
    const query = els.q.value.trim();
    if (query.length < 2) {
      els.results.hidden = true;
      return;
    }
    searchTimer = setTimeout(function () {
      fetch("/api/search/?q=" + encodeURIComponent(query)).then(function (r) { return r.json(); }).then(function (data) {
        els.results.textContent = "";
        data.places.forEach(function (place) {
          const button = document.createElement("button");
          button.type = "button";
          const name = document.createElement("strong");
          name.textContent = place.village;
          const rest = document.createElement("span");
          rest.textContent = place.cell + " · " + place.sector + " · " + place.district;
          button.appendChild(name);
          button.appendChild(rest);
          button.addEventListener("mousedown", function (event) { event.preventDefault(); });
          button.addEventListener("click", function () {
            els.q.value = place.village;
            endSearch(true);
            showPlace(place);
          });
          els.results.appendChild(button);
        });
        els.results.hidden = data.places.length === 0;
      });
    }, 200);
  });

  function locateAt(lat, lon) {
    fetch("/api/locate/?lat=" + encodeURIComponent(lat) + "&lon=" + encodeURIComponent(lon))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.place) showPlace(data.place);
        else bubble("us", data.error || ui.no_fix);
      });
  }

  map.on("click", function (event) { locateAt(event.latlng.lat, event.latlng.lng); });

  document.getElementById("where").addEventListener("click", function () {
    if (!navigator.geolocation) {
      bubble("us", ui.no_geo);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      function (pos) { locateAt(pos.coords.latitude, pos.coords.longitude); },
      function () { bubble("us", ui.no_fix); }
    );
  });

  const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Speech) {
    els.voice.addEventListener("click", function () {
      bubble("us", ui.no_voice);
    });
  } else {
    const ear = new Speech();
    ear.lang = "rw-RW";
    ear.interimResults = false;
    ear.onstart = function () { els.voice.classList.add("live"); els.voice.textContent = ui.hearing; };
    ear.onend = function () { els.voice.classList.remove("live"); els.voice.textContent = ui.voice; };
    ear.onerror = function () {
      bubble("us", ui.not_heard);
    };
    ear.onresult = function (event) {
      const text = event.results[0][0].transcript;
      post("/api/hear/", { text: text, reader: document.body.dataset.reader || "" }).then(function (data) {
        if (!data.ok) {
          bubble("us", data.error || ui.not_heard);
          return;
        }
        applyHeard(data);
      });
    };
    els.voice.addEventListener("click", function () { ear.start(); });
  }

  function savedPlan(plan) {
    const holding = plan.holding || {};
    const portions = holding.portions || {};
    const bits = [];
    (plan.crops || []).forEach(function (id) {
      const row = portions[id] || {};
      const name = cropName(id);
      bits.push(row.target ? name + " " + group(String(row.target).replace(",", ".")) + " kg" : name);
    });
    return plan.village + " · " + bits.join(", ");
  }

  function parseISO(value) {
    const parts = String(value || "").split("-").map(Number);
    return new Date(parts[0], (parts[1] || 1) - 1, parts[2] || 1);
  }

  function isoDate(day) {
    const month = String(day.getMonth() + 1).padStart(2, "0");
    const date = String(day.getDate()).padStart(2, "0");
    return day.getFullYear() + "-" + month + "-" + date;
  }

  function weekKey(value) {
    const day = parseISO(value);
    const utc = new Date(Date.UTC(day.getFullYear(), day.getMonth(), day.getDate()));
    const weekday = utc.getUTCDay() || 7;
    utc.setUTCDate(utc.getUTCDate() + 4 - weekday);
    const yearStart = new Date(Date.UTC(utc.getUTCFullYear(), 0, 1));
    const week = Math.ceil((((utc - yearStart) / 86400000) + 1) / 7);
    return utc.getUTCFullYear() + "-W" + String(week).padStart(2, "0");
  }

  function shiftMonth(value, step) {
    const day = parseISO(value + "-01");
    day.setMonth(day.getMonth() + step);
    return isoDate(day).slice(0, 7);
  }

  function loadPlans(focus) {
    if (!els.plans) return;
    fetch("/api/plans/").then(function (r) { return r.json(); }).then(function (data) {
      state.plans = data.plans || [];
      els.plans.textContent = "";
      if (state.plans.length) {
        const title = document.createElement("h2");
        title.textContent = ui.plans;
        els.plans.appendChild(title);
        state.plans.forEach(function (plan) {
          if (!plan.holding) {
            const line = document.createElement("p");
            line.className = "plan";
            line.textContent = plan.village + " · " + plan.target_crop + " · " + plan.target_kg + " kg/ha";
            els.plans.appendChild(line);
            return;
          }
          const button = document.createElement("button");
          button.type = "button";
          button.className = "plan";
          if (plan.id === state.calendarPlan) button.setAttribute("aria-current", "true");
          button.textContent = savedPlan(plan);
          button.addEventListener("click", function () {
            state.calendarPlan = plan.id;
            state.calendarDay = plan.journey ? plan.journey.today : null;
            loadPlans();
          });
          els.plans.appendChild(button);
        });
      }
      const chosen = state.plans.filter(function (plan) { return plan.journey && plan.id === state.calendarPlan; })[0]
        || state.plans.filter(function (plan) { return plan.journey; })[0];
      if (chosen) state.calendarPlan = chosen.id;
      renderCalendar();
      if (focus && els.calendar) els.calendar.scrollIntoView({ block: "nearest" });
    });
  }

  function renderCalendar() {
    if (!els.calendar) return;
    const plan = state.plans.filter(function (item) { return item.id === state.calendarPlan && item.journey; })[0];
    els.calendar.textContent = "";
    if (!plan) {
      els.calendar.hidden = true;
      return;
    }
    els.calendar.hidden = false;
    const journey = plan.journey;
    const checks = plan.checks || { days: {}, weeks: {} };
    if (!state.calendarDay) state.calendarDay = journey.today;
    const selected = parseISO(state.calendarDay);
    if (selected < parseISO(journey.start) || selected > parseISO(journey.end)) state.calendarDay = journey.today;
    const shown = parseISO(state.calendarDay);
    const monthKey = isoDate(shown).slice(0, 7);
    const months = String(ui.cal_months || "").split(",");
    const weekdays = String(ui.cal_weekdays || "").split(",");

    const heading = document.createElement("h2");
    heading.textContent = ui.cal_title + " · " + plan.village;
    els.calendar.appendChild(heading);
    if (journey.day) {
      const place = document.createElement("p");
      place.className = "cal-place";
      place.textContent = fill(ui.cal_day, { day: journey.day, total: journey.total });
      els.calendar.appendChild(place);
    }
    const choice = document.createElement("p");
    choice.className = "cal-choice";
    choice.textContent = ui.cal_choice;
    els.calendar.appendChild(choice);
    if (plan.marked) {
      const marked = document.createElement("p");
      marked.className = "cal-marked";
      marked.textContent = fill(ui.cal_marked, { n: plan.marked });
      els.calendar.appendChild(marked);
    }

    const bar = document.createElement("div");
    bar.className = "cal-bar";
    const prev = document.createElement("button");
    prev.type = "button";
    prev.textContent = "‹";
    const label = document.createElement("strong");
    label.textContent = (months[shown.getMonth()] || "") + " " + shown.getFullYear();
    const next = document.createElement("button");
    next.type = "button";
    next.textContent = "›";
    const startMonth = journey.start.slice(0, 7);
    const endMonth = journey.end.slice(0, 7);
    prev.disabled = monthKey <= startMonth;
    next.disabled = monthKey >= endMonth;
    prev.addEventListener("click", function () {
      state.calendarDay = shiftMonth(monthKey, -1) + "-01";
      const first = parseISO(state.calendarDay);
      if (first < parseISO(journey.start)) state.calendarDay = journey.start;
      renderCalendar();
    });
    next.addEventListener("click", function () {
      const moved = shiftMonth(monthKey, 1) + "-01";
      state.calendarDay = moved < journey.start ? journey.start : moved;
      if (parseISO(state.calendarDay) > parseISO(journey.end)) state.calendarDay = journey.end;
      renderCalendar();
    });
    bar.appendChild(prev);
    bar.appendChild(label);
    bar.appendChild(next);
    els.calendar.appendChild(bar);

    const grid = document.createElement("div");
    grid.className = "cal-grid";
    weekdays.forEach(function (name) {
      const cell = document.createElement("span");
      cell.textContent = name;
      grid.appendChild(cell);
    });
    const firstOfMonth = new Date(shown.getFullYear(), shown.getMonth(), 1);
    const lead = (firstOfMonth.getDay() + 6) % 7;
    for (let i = 0; i < lead; i += 1) grid.appendChild(document.createElement("span"));
    const count = new Date(shown.getFullYear(), shown.getMonth() + 1, 0).getDate();
    for (let day = 1; day <= count; day += 1) {
      const date = new Date(shown.getFullYear(), shown.getMonth(), day);
      const value = isoDate(date);
      if (value < journey.start || value > journey.end) {
        const plain = document.createElement("span");
        plain.textContent = String(day);
        plain.className = "out";
        grid.appendChild(plain);
        continue;
      }
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = String(day);
      if (value === journey.today) button.classList.add("today");
      if (value === state.calendarDay) button.classList.add("picked");
      if ((checks.days || {})[value] && (checks.days || {})[value].length) button.classList.add("marked");
      button.addEventListener("click", function () {
        state.calendarDay = value;
        renderCalendar();
      });
      grid.appendChild(button);
    }
    els.calendar.appendChild(grid);

    const dayTitle = document.createElement("h3");
    const monthName = months[shown.getMonth()] || "";
    dayTitle.textContent = (state.calendarDay === journey.today ? ui.cal_today + " · " : "") + shown.getDate() + " " + monthName;
    els.calendar.appendChild(dayTitle);

    function ticks(items, prefix, scope) {
      (items || []).forEach(function (line, index) {
        const id = prefix + index;
        const row = document.createElement("label");
        row.className = "tick";
        const box = document.createElement("input");
        box.type = "checkbox";
        const bucket = scope === "week" ? (checks.weeks || {})[weekKey(state.calendarDay)] : (checks.days || {})[state.calendarDay];
        box.checked = (bucket || []).indexOf(id) >= 0;
        box.addEventListener("change", function () {
          post("/api/plans/" + plan.id + "/check/", {
            date: state.calendarDay,
            item: id,
            on: box.checked,
          }).then(function (data) {
            if (!data.ok || !data.plan) {
              box.checked = !box.checked;
              return;
            }
            state.plans = state.plans.map(function (item) { return item.id === data.plan.id ? data.plan : item; });
            renderCalendar();
          });
        });
        const text = document.createElement("span");
        text.textContent = line[lang] || line.en;
        row.appendChild(box);
        row.appendChild(text);
        els.calendar.appendChild(row);
      });
    }
    ticks(journey.daily, "d", "day");
    if ((journey.weekly || []).length) {
      const week = document.createElement("h3");
      week.textContent = ui.cal_week;
      els.calendar.appendChild(week);
      ticks(journey.weekly, "w", "week");
    }
  }

  fetch("/api/boundaries/").then(function (r) { return r.json(); }).then(function (data) {
    outlines = L.geoJSON(data, {
      style: { color: "#1b4332", weight: 1, fillColor: "#95d5b2", fillOpacity: 0.04 },
      onEachFeature: function (_, layer) {
        layer.on("click", function (event) {
          L.DomEvent.stopPropagation(event);
          locateAt(event.latlng.lat, event.latlng.lng);
        });
      },
    }).addTo(map);
  });

  if (els.go) els.go.addEventListener("click", openPopup);
  const lock = lockedOffice();
  if (lock && readerId() === "sector") {
    showPlace({
      district: lock.district,
      sector: lock.sector,
      sector_id: lock.sector_id,
      lat: lock.lat,
      lon: lock.lon,
    });
  }
  paintCrops();
  syncJourney();
  loadPlans();
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closePopup(true);
  });
})();
