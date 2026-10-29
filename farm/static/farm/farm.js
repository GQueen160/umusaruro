(function () {
  "use strict";

  const crops = JSON.parse(document.getElementById("crop-data").textContent);
  const ui = JSON.parse(document.getElementById("ui-copy").textContent);
  const lang = document.body.dataset.lang || "en";
  const token = document.querySelector('meta[name="csrf-token"]').content;
  const state = { place: null, crops: [], advice: null, request: 0 };
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
    voice: document.getElementById("voice"),
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

  function showPlace(place) {
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
    if (state.crops.length) loadAdvice();
  }

  function loadAdvice() {
    if (!state.place || !state.place.district || !state.crops.length) return;
    const mine = ++state.request;
    post("/api/advice/", { district: state.place.district, crops: state.crops, reader: document.body.dataset.reader || "" }).then(function (data) {
      if (mine !== state.request || !data.advice) return;
      state.advice = data.advice;
      renderAdvice(data.advice);
    });
  }

  function renderAdvice(advice) {
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
    down.addEventListener("click", function () { input.value = String(Math.max(100, Number(input.value) - 100)); });
    up.addEventListener("click", function () { input.value = String(Number(input.value) + 100); });
    const save = document.createElement("button");
    save.id = "save";
    save.type = "submit";
    save.textContent = "Bika intego";
    row.appendChild(down);
    row.appendChild(input);
    row.appendChild(up);
    els.target.appendChild(title);
    els.target.appendChild(why);
    els.target.appendChild(row);
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

  function loadPlans() {
    if (!els.plans) return;
    fetch("/api/plans/").then(function (r) { return r.json(); }).then(function (data) {
      els.plans.textContent = "";
      if (!data.plans.length) return;
      const title = document.createElement("h2");
      title.textContent = ui.plans;
      els.plans.appendChild(title);
      data.plans.forEach(function (plan) {
        const line = document.createElement("p");
        line.className = "plan";
        line.textContent = plan.village + " · " + plan.target_crop + " · " + plan.target_kg + " kg/ha";
        els.plans.appendChild(line);
      });
    });
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

  paintCrops();
  loadPlans();
})();
