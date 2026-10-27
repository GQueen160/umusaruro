(function () {
  "use strict";

  const crops = JSON.parse(document.getElementById("crop-data").textContent);
  const token = document.querySelector('meta[name="csrf-token"]').content;
  const state = { place: null, crops: [], advice: null, request: 0 };
  const pin = L.divIcon({ className: "", html: '<div class="pin"></div>', iconSize: [22, 22] });
  let marker = null;
  let outlines = null;

  const map = L.map("map", { zoomControl: false }).setView([-1.95, 29.9], 8);
  L.control.zoom({ position: "bottomright" }).addTo(map);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
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
    label.textContent = who === "you" ? "Wowe" : "Umusaruro";
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
    if (!place.village_id) {
      const small = document.createElement("small");
      small.textContent = "Kanda umudugudu wawe. Tap your village.";
      els.place.appendChild(small);
    }
    fly(place, place.village_id ? 15 : 11);
    if (state.crops.length) loadAdvice();
  }

  function loadAdvice() {
    if (!state.place || !state.place.district || !state.crops.length) return;
    const mine = ++state.request;
    post("/api/advice/", { district: state.place.district, crops: state.crops }).then(function (data) {
      if (mine !== state.request || !data.advice) return;
      state.advice = data.advice;
      renderAdvice(data.advice);
    });
  }

  function renderAdvice(advice) {
    els.advice.textContent = "";
    const note = document.createElement("p");
    note.className = "note";
    note.textContent = advice.note_rw;
    els.advice.appendChild(note);
    advice.cards.forEach(function (card) {
      const box = document.createElement("article");
      box.className = "card " + card.kind;
      const title = document.createElement("h2");
      title.textContent = card.title_rw;
      const en = document.createElement("p");
      en.className = "en";
      en.textContent = card.title_en;
      const body = document.createElement("p");
      body.textContent = card.body_rw;
      box.appendChild(title);
      box.appendChild(en);
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
          item.appendChild(document.createTextNode(" " + fact.label));
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
    els.target.textContent = "";
    if (!target) {
      els.target.hidden = true;
      return;
    }
    els.target.hidden = false;
    const title = document.createElement("h2");
    title.textContent = "Intego: " + target.rw;
    const why = document.createElement("p");
    why.textContent = target.why_rw;
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
        bubble("us", "Banza ukande umudugudu ku karita.");
        return;
      }
      post("/api/plans/save/", {
        village_id: state.place.village_id,
        crops: state.crops,
        target_crop: target.crop,
        target_kg: input.value,
      }).then(function (data) {
        if (!data.ok) {
          bubble("us", data.error || "Ntibyakunze.");
          return;
        }
        bubble("us", "Intego yabitswe: " + data.plan.target_kg + " kg kuri hegitari muri " + data.plan.village + ".");
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
      button.textContent = crop.rw;
      const en = document.createElement("small");
      en.textContent = crop.en;
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
    bubble("us", data.reply_rw);
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
    fillSelect(picks.district, data.places, "Hitamo akarere");
  });

  picks.district.addEventListener("change", function () {
    const option = picks.district.selectedOptions[0];
    fillSelect(picks.sector, [], "Hitamo umurenge");
    fillSelect(picks.cell, [], "Hitamo akagari");
    fillSelect(picks.village, [], "Hitamo umudugudu");
    if (!option || !option.dataset.place) return;
    const place = JSON.parse(option.dataset.place);
    showPlace({ district: place.name, lat: place.lat, lon: place.lon, village_id: "" });
    fetch("/api/places/?district=" + encodeURIComponent(place.name)).then(function (r) { return r.json(); }).then(function (data) {
      fillSelect(picks.sector, data.places, "Hitamo umurenge");
    });
  });

  picks.sector.addEventListener("change", function () {
    const option = picks.sector.selectedOptions[0];
    fillSelect(picks.cell, [], "Hitamo akagari");
    fillSelect(picks.village, [], "Hitamo umudugudu");
    if (!option || !option.value) return;
    const place = JSON.parse(option.dataset.place);
    showPlace({ district: state.place.district, sector: place.name, sector_id: place.id, lat: place.lat, lon: place.lon, village_id: "" });
    fetch("/api/places/?sector_id=" + encodeURIComponent(place.id)).then(function (r) { return r.json(); }).then(function (data) {
      fillSelect(picks.cell, data.places, "Hitamo akagari");
    });
  });

  picks.cell.addEventListener("change", function () {
    const option = picks.cell.selectedOptions[0];
    fillSelect(picks.village, [], "Hitamo umudugudu");
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
      fillSelect(picks.village, data.places, "Hitamo umudugudu");
    });
  });

  picks.village.addEventListener("change", function () {
    const option = picks.village.selectedOptions[0];
    if (!option || !option.dataset.place) return;
    showPlace(JSON.parse(option.dataset.place));
  });

  let searchTimer = 0;
  els.q.addEventListener("input", function () {
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
          button.addEventListener("click", function () {
            els.results.hidden = true;
            els.q.value = place.village;
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
        else bubble("us", data.error || "Ntabwo nabonye ahantu.");
      });
  }

  map.on("click", function (event) { locateAt(event.latlng.lat, event.latlng.lng); });

  document.getElementById("where").addEventListener("click", function () {
    if (!navigator.geolocation) {
      bubble("us", "Iyi mudasobwa ntayerekana aho uri. Kanda ku karita.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      function (pos) { locateAt(pos.coords.latitude, pos.coords.longitude); },
      function () { bubble("us", "Ntabwo nabonye aho uri. Kanda ku karita."); }
    );
  });

  const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Speech) {
    els.voice.addEventListener("click", function () {
      bubble("us", "Iyi mudasobwa ntumva ijwi. Koresha amagambo cyangwa kanda ku karita.");
    });
  } else {
    const ear = new Speech();
    ear.lang = "rw-RW";
    ear.interimResults = false;
    ear.onstart = function () { els.voice.classList.add("live"); els.voice.textContent = "Ndumva…"; };
    ear.onend = function () { els.voice.classList.remove("live"); els.voice.textContent = "Vuga"; };
    ear.onerror = function () {
      bubble("us", "Ntabwo numvise. Ongera uvuge, cyangwa andika izina ry'umudugudu.");
    };
    ear.onresult = function (event) {
      const text = event.results[0][0].transcript;
      post("/api/hear/", { text: text }).then(function (data) {
        if (!data.ok) {
          bubble("us", data.error || "Ntabwo numvise.");
          return;
        }
        applyHeard(data);
      });
    };
    els.voice.addEventListener("click", function () { ear.start(); });
  }

  function loadPlans() {
    fetch("/api/plans/").then(function (r) { return r.json(); }).then(function (data) {
      els.plans.textContent = "";
      if (!data.plans.length) return;
      const title = document.createElement("h2");
      title.textContent = "Intego wabitse";
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
