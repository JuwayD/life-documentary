// 人生纪实 · 明朝篇 — 前端逻辑 (PixiJS 视口 + WebSocket 流式)
"use strict";

const $ = (sel) => document.querySelector(sel);
const chat = $("#chat");
const inputEl = $("#input");
const submitBtn = $("#submit");
const statusEl = $("#status");
const form = $("#input-form");

// ===================================================================
// PixiJS scene renderer
// ===================================================================
let app = null;
let sceneContainer = null;
let entitySprites = {};   // entity_id -> PIXI.Container
let tileSprites = [];     // current location tiles
let lastSnapshot = null;
let lastRenderSignature = null;
let currentLocation = null;
window.__renderSceneStats = { draws: 0, skips: 0 };

const TILE_W = 64;
const TILE_H = 32;

// Placeholder tile colors
const TILE_COLORS = {
  stone_floor: 0x888877,
  wood_floor: 0x8b7355,
  wall: 0x5c5c4c,
  door: 0x6b4c3b,
  dirt: 0x8b864e,
  default: 0x666655,
};

const ENTITY_COLORS = {
  player: 0x4a90d9,
  npc: 0xcc6644,
  official: 0xcc3333,
};

function tileColorForLocation(loc) {
  const t = (loc.tags || []).join(" ");
  if (t.includes("outdoor") || t.includes("market")) return TILE_COLORS.dirt;
  if (t.includes("official")) return TILE_COLORS.stone_floor;
  if (t.includes("indoor") && t.includes("inn")) return TILE_COLORS.wood_floor;
  return TILE_COLORS.default;
}

function findLocationName(state, locationId) {
  if (!state || !locationId) return null;
  const loc = (state.locations || []).find((l) => l.id === locationId);
  return loc ? loc.name : null;
}

function initPixi() {
  if (app) return;
  const el = $("#viewport");
  if (!el) return;

  app = new PIXI.Application();
  app.init({
    resizeTo: el,
    backgroundColor: 0x1a1612,
    antialias: false,
  }).then(() => {
    el.appendChild(app.canvas);
    sceneContainer = new PIXI.Container();
    app.stage.addChild(sceneContainer);
    window.__rendererReady = true;
    if (lastSnapshot) renderScene(lastSnapshot);
  });
}

// iso projection: grid (col, row) -> screen (x, y)
function isoToScreen(col, row) {
  const cx = (col - row) * (TILE_W / 2);
  const cy = (col + row) * (TILE_H / 2);
  return { x: cx, y: cy };
}

function screenToIso(sx, sy, gridW, gridH) {
  // rough inverse
  const col = (sx / (TILE_W / 2) + sy / (TILE_H / 2)) / 2;
  const row = (sy / (TILE_H / 2) - sx / (TILE_W / 2)) / 2;
  return { col: Math.round(col), row: Math.round(row) };
}

function drawTile(col, row, color) {
  const g = new PIXI.Graphics();
  const { x, y } = isoToScreen(col, row);

  // diamond shape
  g.poly([
    x, y - TILE_H / 2,
    x + TILE_W / 2, y,
    x, y + TILE_H / 2,
    x - TILE_W / 2, y,
  ]);
  g.fill({ color });
  // subtle border
  g.stroke({ width: 0.5, color: 0x333322 });

  return g;
}

function drawEntitySprite(entity) {
  const c = new PIXI.Container();
  const color = entity.id === "player"
    ? ENTITY_COLORS.player
    : (entity.tags || []).includes("official") ? ENTITY_COLORS.official : ENTITY_COLORS.npc;

  // body circle
  const body = new PIXI.Graphics();
  body.circle(0, -8, 10);
  body.fill({ color });

  // direction indicator
  const dir = new PIXI.Graphics();
  dir.moveTo(0, -18);
  dir.lineTo(-4, -28);
  dir.lineTo(4, -28);
  dir.closePath();
  dir.fill({ color });

  c.addChild(body);
  c.addChild(dir);

  // name label
  const label = new PIXI.Text({
    text: entity.name,
    style: {
      fontFamily: "PingFang SC, sans-serif",
      fontSize: 11,
      fill: 0xf4ecd8,
      align: "center",
      dropShadow: { color: 0x000000, alpha: 0.7, blur: 2, distance: 1 },
    },
  });
  label.anchor.set(0.5, 1);
  label.y = -32;
  c.addChild(label);

  // HP bar background
  const hpBg = new PIXI.Graphics();
  hpBg.rect(-15, -42, 30, 4);
  hpBg.fill({ color: 0x333333 });
  c.addChild(hpBg);

  // HP bar fill
  const maxHp = (entity.attributes || {}).max_hp || 100;
  const hp = Math.max(0, (entity.attributes || {}).hp || 0);
  const hpPct = Math.min(1, hp / maxHp);
  const hpFill = new PIXI.Graphics();
  const hpColor = hpPct > 0.5 ? 0x6c8d3f : hpPct > 0.25 ? 0xc2944a : 0xcc3333;
  hpFill.rect(-15, -42, 30 * hpPct, 4);
  hpFill.fill({ color: hpColor });
  c.addChild(hpFill);

  // Store entity data for updates
  c._entity = entity;
  c._hpFill = hpFill;

  return c;
}

function updateEntitySprite(c, entity) {
  if (!c || !c._hpFill) return;
  const maxHp = (entity.attributes || {}).max_hp || 100;
  const hp = Math.max(0, (entity.attributes || {}).hp || 0);
  const hpPct = Math.min(1, hp / maxHp);
  const hpColor = hpPct > 0.5 ? 0x6c8d3f : hpPct > 0.25 ? 0xc2944a : 0xcc3333;
  c._hpFill.clear();
  c._hpFill.rect(-15, -42, 30 * hpPct, 4);
  c._hpFill.fill({ color: hpColor });
}

function renderSignature(snapshot) {
  const player = (snapshot.entities || []).find((e) => e.id === "player");
  const playerLocation = player ? player.location : "";
  const loc = (snapshot.locations || []).find((l) => l.id === playerLocation) || {};
  const entities = (snapshot.entities || [])
    .filter((e) => e.location === playerLocation)
    .map((e) => {
      const attrs = e.attributes || {};
      const pos = e.pos || [5, 5];
      const tags = (e.tags || []).join(",");
      return [e.id, e.name, e.type, e.location, pos[0], pos[1], attrs.hp, attrs.max_hp, tags].join(":");
    })
    .sort();
  return JSON.stringify({
    location: playerLocation,
    size: loc.size || [10, 10],
    exits: loc.exits || {},
    tags: loc.tags || [],
    entities,
  });
}

function renderScene(snapshot) {
  if (!app || !sceneContainer) return;
  lastSnapshot = snapshot;

  // Find player's current location
  const player = snapshot.entities.find((e) => e.id === "player");
  if (!player) return;

  const loc = snapshot.locations.find((l) => l.id === player.location);
  if (!loc) return;

  const signature = renderSignature(snapshot);
  if (signature === lastRenderSignature) {
    window.__renderSceneStats.skips += 1;
    return;
  }
  lastRenderSignature = signature;
  window.__renderSceneStats.draws += 1;

  const locSignature = JSON.stringify({ id: loc.id, size: loc.size || [10, 10], exits: loc.exits || {}, tags: loc.tags || [] });
  const locChanged = currentLocation !== locSignature;
  currentLocation = locSignature;

  if (locChanged) {
    // Clear and redraw tiles
    sceneContainer.removeChildren();
    tileSprites = [];
    entitySprites = {};

    const [gridW, gridH] = loc.size || [10, 10];
    const tileColor = tileColorForLocation(loc);

    // Draw exits as special tiles
    const exitDirs = new Set(Object.keys(loc.exits || {}));
    const exitColors = {
      north: 0x6b4c3b,
      south: 0x6b4c3b,
      east: 0x6b4c3b,
      west: 0x6b4c3b,
    };

    for (let row = 0; row < gridH; row++) {
      for (let col = 0; col < gridW; col++) {
        let color = tileColor;
        // Mark exit tiles
        if (row === 0 && exitDirs.has("north")) color = exitColors.north;
        if (row === gridH - 1 && exitDirs.has("south")) color = exitColors.south;
        if (col === gridW - 1 && exitDirs.has("east")) color = exitColors.east;
        if (col === 0 && exitDirs.has("west")) color = exitColors.west;

        const tile = drawTile(col, row, color);
        tile.zIndex = col + row; // depth sort
        sceneContainer.addChild(tile);
        tileSprites.push(tile);
      }
    }

    // Place entities
    const nearby = snapshot.entities.filter((e) => e.location === loc.id);
    for (const ent of nearby) {
      const spr = drawEntitySprite(ent);
      const [ex, ey] = ent.pos || [5, 5];
      const { x, y } = isoToScreen(ex, ey);
      spr.x = x;
      spr.y = y;
      spr.zIndex = ex + ey + 100; // above tiles
      sceneContainer.addChild(spr);
      entitySprites[ent.id] = spr;
    }
  } else {
    // Same location — update entity positions/sprites
    const nearby = snapshot.entities.filter((e) => e.location === loc.id);
    for (const ent of nearby) {
      const [ex, ey] = ent.pos || [5, 5];
      const { x, y } = isoToScreen(ex, ey);
      let spr = entitySprites[ent.id];
      if (!spr) {
        spr = drawEntitySprite(ent);
        spr.zIndex = ex + ey + 100;
        sceneContainer.addChild(spr);
        entitySprites[ent.id] = spr;
      }
      spr.x = x;
      spr.y = y;
      spr.zIndex = ex + ey + 100;
      updateEntitySprite(spr, ent);
    }
    // Remove sprites for entities that left
    const nearbyIds = new Set(nearby.map((e) => e.id));
    for (const [eid, spr] of Object.entries(entitySprites)) {
      if (!nearbyIds.has(eid)) {
        sceneContainer.removeChild(spr);
        delete entitySprites[eid];
      }
    }
  }

  // Center viewport on player
  const [px, py] = player.pos || [5, 5];
  const playerScreen = isoToScreen(px, py);
  const vw = app.renderer.width;
  const vh = app.renderer.height;
  sceneContainer.x = vw / 2 - playerScreen.x;
  sceneContainer.y = vh / 2 - playerScreen.y;
}

// ===================================================================
// Combat feedback
// ===================================================================
function flashEntity(entityId, durationMs) {
  const spr = entitySprites[entityId];
  if (!spr) return;
  // Flash red by overlaying a red tint via graphics
  const flash = new PIXI.Graphics();
  flash.circle(0, -8, 12);
  flash.fill({ color: 0xff0000, alpha: 0.5 });
  spr.addChild(flash);
  setTimeout(() => spr.removeChild(flash), durationMs);
}

function showFloatText(entityId, text) {
  const spr = entitySprites[entityId];
  if (!spr || !app) return;
  // Convert sprite position to viewport screen coords
  const globalPos = spr.getGlobalPosition();
  const viewportEl = $("#viewport");
  const rect = viewportEl.getBoundingClientRect();
  const sx = rect.left + globalPos.x + sceneContainer.x;
  const sy = rect.top + globalPos.y + sceneContainer.y;

  const el = document.createElement("div");
  el.className = "float-text";
  el.textContent = text;
  el.style.left = sx + "px";
  el.style.top = sy + "px";
  document.body.appendChild(el);
  el.addEventListener("animationend", () => el.remove());
}

// ===================================================================
// Chat & narration
// ===================================================================
function addBubble(role, text, label) {
  const div = document.createElement("div");
  div.className = `bubble ${role}`;
  div.setAttribute("data-test", `bubble-${role}`);
  if (label) {
    const span = document.createElement("span");
    span.className = "label";
    span.textContent = label;
    div.appendChild(span);
  }
  const body = document.createElement("div");
  body.textContent = text;
  div.appendChild(body);
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

let streamBubble = null;
function startStreamBubble() {
  streamBubble = addBubble("gm", "", "GM");
  return streamBubble;
}
function appendStream(text) {
  if (!streamBubble) return;
  const body = streamBubble.querySelector("div:last-child");
  if (body) {
    body.textContent += text;
  }
  chat.scrollTop = chat.scrollHeight;
}
function finishStreamBubble() {
  streamBubble = null;
}

function setStatus(text) {
  statusEl.textContent = text;
}

function setBusy(busy) {
  submitBtn.disabled = busy;
  inputEl.disabled = busy;
  submitBtn.textContent = busy ? "思考中..." : "行动";
}

function downloadJson(filename, data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  downloadBlob(filename, blob);
}

function downloadText(filename, text) {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  downloadBlob(filename, blob);
}

function downloadBlob(filename, blob) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

// ===================================================================
// WebSocket turn handler (with REST fallback)
// ===================================================================
let ws = null;
let wsReconnectTimer = null;
let birthTemplates = [];
let selectedBirthTemplateId = null;

let debugTestSnapshots = [];
let debugTestSnapshotSummary = { snapshot_count: 0, totals: {}, latest_updated_at: "" };
let debugTestPresets = [];
let debugSnapshotDiffs = {};
let debugSnapshotDetails = {};
let debugSnapshotLoadConfirmations = {};
let debugSnapshotBundleImportPreview = null;
let debugSnapshotHealth = null;
let debugSnapshotQuery = "";
let debugSnapshotTagFilter = "";
let debugSnapshotShowArchived = false;
let debugSnapshotSort = "updated_desc";
let debugSnapshotSelectedIds = new Set();
let debugToolFilter = "";
let debugToolQuery = "";

function connectWS() {
  if (ws && ws.readyState === WebSocket.OPEN) return;
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${proto}//${location.host}/ws/turn`;
  ws = new WebSocket(url);
  ws.onopen = () => {
    if (wsReconnectTimer) { clearTimeout(wsReconnectTimer); wsReconnectTimer = null; }
  };
  ws.onclose = () => {
    // auto-reconnect
    wsReconnectTimer = setTimeout(connectWS, 3000);
  };
}

async function handleTurn(text) {
  addBubble("player", text, "你");
  setBusy(true);
  setStatus("GM 正在思考...");
  startStreamBubble();

  // Try WebSocket first, fall back to REST
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ input: text }));
  } else {
    // REST fallback
    try {
      const res = await api("/api/turn", {
        method: "POST",
        body: JSON.stringify({ input: text }),
      });
      appendStream(res.narration);
      finishStreamBubble();
      renderSidePanel(res.state);
      renderScene(res.state);
      setStatus("");
    } catch (e) {
      addBubble("system", `出错: ${e.message}`);
      setStatus("");
    } finally {
      setBusy(false);
      inputEl.focus();
    }
    return;
  }

  // Set up one-shot handler for this turn
  function onMsg(evt) {
    const event = JSON.parse(evt.data);

    switch (event.type) {
      case "text":
        appendStream(event.content);
        break;
      case "tool_call":
        setStatus(`调用工具: ${event.name}`);
        break;
      case "tool_result":
        setStatus("");
        break;
      case "done":
        finishStreamBubble();
        renderSidePanel(event.state);
        renderScene(event.state);
        setStatus("");
        setBusy(false);
        inputEl.focus();
        ws.removeEventListener("message", onMsg);
        break;
      case "error":
        appendStream(`\n(出错: ${event.message})`);
        finishStreamBubble();
        setStatus("");
        setBusy(false);
        inputEl.focus();
        ws.removeEventListener("message", onMsg);
        break;
      case "state":
        renderSidePanel(event.state);
        break;
    }
  }
  ws.addEventListener("message", onMsg);
}

// ===================================================================
// REST API helper
// ===================================================================
async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      msg = body.detail || msg;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}

// ===================================================================
// Side panel rendering
// ===================================================================
const PANEL_STATE_KEY = "mingrpg.panelCollapsed";
const DENSITY_KEY = "mingrpg.infoDensity";
let currentDensity = loadDensityMode();
let lastSidePanelState = null;
let panelSearchQuery = "";
let sideNavScrollLockUntil = 0;
const PANEL_SEARCH_HIGHLIGHT_CLASS = "panel-search-highlight";
const panelContentSignatures = {};
const SIDE_NAV_UPDATE_GROUPS = {
  time: ["time", "summary", "priority", "recent", "gaps", "player", "location", "nearby", "relationships"],
  suggestions: ["suggestions"],
  story: ["party", "advisor", "observation", "story", "clues", "pressure", "ending", "skills", "evolutions"],
  review: ["timeline", "review"],
};
const SIDE_NAV_ORDER = ["time", "suggestions", "story", "review"];

function loadDensityMode() {
  return localStorage.getItem(DENSITY_KEY) === "compact" ? "compact" : "detailed";
}

function applyDensityMode(mode) {
  currentDensity = mode === "compact" ? "compact" : "detailed";
  document.body.classList.toggle("density-compact", currentDensity === "compact");
  document.querySelectorAll("[data-density-mode]").forEach((btn) => {
    const active = btn.dataset.densityMode === currentDensity;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-pressed", active ? "true" : "false");
  });
}

function initDensityToggle() {
  applyDensityMode(currentDensity);
  document.querySelectorAll("[data-density-mode]").forEach((btn) => {
    btn.addEventListener("click", () => {
      applyDensityMode(btn.dataset.densityMode);
      localStorage.setItem(DENSITY_KEY, currentDensity);
      if (lastSidePanelState) renderSidePanel(lastSidePanelState);
    });
  });
}

function setMobilePanelOpen(open) {
  document.body.classList.toggle("side-panel-open", open);
  const btn = $("#btn-mobile-panel");
  if (btn) btn.setAttribute("aria-expanded", open ? "true" : "false");
}

function initMobilePanelToggle() {
  const btn = $("#btn-mobile-panel");
  const backdrop = $("#side-panel-backdrop");
  if (!btn || !backdrop) return;
  btn.addEventListener("click", () => {
    setMobilePanelOpen(!document.body.classList.contains("side-panel-open"));
  });
  backdrop.addEventListener("click", () => setMobilePanelOpen(false));
}

function isCompactDensity() {
  return currentDensity === "compact";
}

function loadPanelState() {
  try {
    return JSON.parse(localStorage.getItem(PANEL_STATE_KEY) || "{}");
  } catch {
    return {};
  }
}

function savePanelState(state) {
  localStorage.setItem(PANEL_STATE_KEY, JSON.stringify(state));
}

function setPanelCollapsed(section, collapsed) {
  section.classList.toggle("collapsed", collapsed);
  const toggle = section.querySelector("[data-panel-toggle]");
  if (toggle) toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
  if (!collapsed) clearPanelUpdate(section);
  updateSideNavUpdateSummary();
  updatePanelContextNotice();
}

function clearPanelUpdate(section) {
  section.classList.remove("has-update");
  const badge = section.querySelector("[data-panel-update-badge]");
  if (badge) badge.remove();
  updateSideNavUpdateSummary();
}

function markPanelUpdated(section) {
  if (section.classList.contains("has-update")) return;
  section.classList.add("has-update");
  const toggle = section.querySelector("[data-panel-toggle]");
  if (!toggle) return;
  const badge = document.createElement("span");
  badge.className = "panel-update-badge";
  badge.setAttribute("data-panel-update-badge", "");
  badge.setAttribute("data-test", `panel-update-${section.dataset.panelSection}`);
  badge.textContent = "更新";
  toggle.appendChild(badge);
  updateSideNavUpdateSummary();
}

function updateCollapsedPanelBadges() {
  document.querySelectorAll("[data-panel-section]").forEach((section) => {
    const id = section.dataset.panelSection;
    const body = section.querySelector("[data-panel-body]");
    if (!id || !body) return;
    const signature = body.textContent.trim();
    const previous = panelContentSignatures[id];
    panelContentSignatures[id] = signature;
    if (previous === undefined || previous === signature) return;
    if (section.classList.contains("collapsed")) markPanelUpdated(section);
  });
  updateSideNavUpdateSummary();
}

function countUpdatedPanels(ids) {
  return ids.reduce((count, id) => {
    const section = document.querySelector(`[data-panel-section="${id}"]`);
    return count + (section && section.classList.contains("has-update") ? 1 : 0);
  }, 0);
}

function updateSideNavUpdateSummary() {
  Object.entries(SIDE_NAV_UPDATE_GROUPS).forEach(([navId, panelIds]) => {
    const btn = document.querySelector(`[data-side-nav="${navId}"]`);
    if (!btn) return;
    const count = countUpdatedPanels(panelIds);
    btn.classList.toggle("has-update", count > 0);
    let badge = btn.querySelector("[data-side-nav-update-badge]");
    if (count === 0) {
      if (badge) badge.remove();
      return;
    }
    if (!badge) {
      badge = document.createElement("span");
      badge.className = "side-nav-update-badge";
      badge.setAttribute("data-side-nav-update-badge", "");
      badge.setAttribute("data-test", `side-nav-update-${navId}`);
      btn.appendChild(badge);
    }
    badge.textContent = `${count}新`;
  });
}

function applyPanelState() {
  const state = loadPanelState();
  document.querySelectorAll("[data-panel-section]").forEach((section) => {
    const id = section.dataset.panelSection;
    setPanelCollapsed(section, state[id] === true);
  });
}

function initPanelToggles() {
  applyPanelState();
  document.querySelectorAll("[data-panel-toggle]").forEach((toggle) => {
    toggle.addEventListener("click", () => {
      const id = toggle.dataset.panelToggle;
      const section = document.querySelector(`[data-panel-section="${id}"]`);
      if (!section) return;
      const state = loadPanelState();
      const collapsed = !section.classList.contains("collapsed");
      setPanelCollapsed(section, collapsed);
      state[id] = collapsed;
      savePanelState(state);
    });
  });
}

function initPanelBulkControls() {
  document.querySelectorAll("[data-panel-bulk]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const collapse = btn.dataset.panelBulk === "collapse";
      const state = loadPanelState();
      document.querySelectorAll("[data-panel-section]").forEach((section) => {
        const id = section.dataset.panelSection;
        setPanelCollapsed(section, collapse);
        state[id] = collapse;
      });
      savePanelState(state);
    });
  });
}

function initSideNav() {
  document.querySelectorAll("[data-side-nav]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.sideNav;
      const targetId = (SIDE_NAV_UPDATE_GROUPS[id] || [])
        .find((panelId) => {
          const panel = document.querySelector(`[data-panel-section="${panelId}"]`);
          return panel && panel.classList.contains("has-update");
        }) || id;
      setActiveSideNav(id);
      focusPanelSection(targetId);
    });
  });
  const sidePanel = $("#side-panel");
  if (sidePanel) {
    sidePanel.addEventListener("scroll", updateActiveSideNavFromScroll, { passive: true });
  }
  updateActiveSideNavFromScroll();
}

function setActiveSideNav(id) {
  document.querySelectorAll("[data-side-nav]").forEach((btn) => {
    const active = btn.dataset.sideNav === id;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-current", active ? "true" : "false");
  });
}

function sideNavGroupForPanel(panelId) {
  return SIDE_NAV_ORDER.find((navId) => (SIDE_NAV_UPDATE_GROUPS[navId] || []).includes(panelId)) || "time";
}

function updateActiveSideNavFromScroll() {
  if (Date.now() < sideNavScrollLockUntil) return;
  const sidePanel = $("#side-panel");
  if (!sidePanel) return;
  const panelTop = sidePanel.getBoundingClientRect().top;
  let activePanelId = "time";
  document.querySelectorAll("[data-panel-section]:not(.search-hidden)").forEach((section) => {
    const rect = section.getBoundingClientRect();
    if (rect.top <= panelTop + 64) activePanelId = section.dataset.panelSection || activePanelId;
  });
  setActiveSideNav(sideNavGroupForPanel(activePanelId));
}

function initPanelSearch() {
  const input = $("#panel-search-input");
  if (!input) return;
  input.addEventListener("input", () => {
    panelSearchQuery = input.value.trim().toLowerCase();
    applyPanelSearch();
  });
  document.addEventListener("keydown", (ev) => {
    if ((ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === "k") {
      ev.preventDefault();
      input.focus();
      input.select();
    }
  });
}

function applyPanelSearch() {
  const empty = $("#panel-search-empty");
  const countEl = $("#panel-search-count");
  const resultsEl = $("#panel-search-results");
  const query = panelSearchQuery;
  let matched = 0;
  let total = 0;
  const matches = [];
  document.querySelectorAll("[data-panel-section]").forEach((section) => {
    total += 1;
    clearPanelSearchHighlights(section);
    if (!query) {
      section.classList.remove("search-hidden");
      matched += 1;
      return;
    }
    const title = section.querySelector("[data-panel-toggle]")?.childNodes[0]?.textContent.trim() || section.dataset.panelSection || "面板";
    const body = section.querySelector("[data-panel-body]");
    const text = section.textContent.replace(/\s+/g, " ").trim();
    const bodyText = (body ? body.textContent : section.textContent).replace(/\s+/g, " ").trim();
    const lower = text.toLowerCase();
    const titleMatch = title.toLowerCase().includes(query);
    const isMatch = lower.includes(query);
    section.classList.toggle("search-hidden", !isMatch);
    if (isMatch) {
      matched += 1;
      matches.push({ id: section.dataset.panelSection, title, titleMatch, snippet: buildSearchSnippet(bodyText, query) });
      highlightPanelSearchMatches(section, query);
    }
  });
  if (countEl) {
    countEl.textContent = query
      ? `匹配 ${matched} / ${total} 个面板`
      : `共 ${total} 个面板`;
  }
  renderPanelSearchResults(resultsEl, matches, query);
  if (empty) empty.classList.toggle("hidden", !query || matched > 0);
  updatePanelContextNotice();
}

function updatePanelContextNotice() {
  const notice = $("#panel-context-notice");
  if (!notice) return;
  const total = document.querySelectorAll("[data-panel-section]").length;
  const hiddenBySearch = panelSearchQuery
    ? document.querySelectorAll("[data-panel-section].search-hidden").length
    : 0;
  const collapsed = document.querySelectorAll("[data-panel-section].collapsed").length;
  const actions = [];
  const notes = [];
  if (hiddenBySearch > 0) {
    notes.push(`搜索已隐藏 ${hiddenBySearch}/${total} 个面板`);
    actions.push(`<button type="button" data-panel-context-action="clear-search" data-test="panel-context-clear-search">清除搜索</button>`);
  }
  if (collapsed > 0) {
    notes.push(`${collapsed} 个面板已折叠`);
    actions.push(`<button type="button" data-panel-context-action="expand-all" data-test="panel-context-expand-all">全部展开</button>`);
  }
  if (notes.length === 0) {
    notice.classList.add("hidden");
    notice.innerHTML = "";
    return;
  }
  notice.classList.remove("hidden");
  notice.innerHTML = `<span>${notes.join(" · ")}</span>${actions.join("")}`;
  notice.querySelectorAll("[data-panel-context-action]").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (btn.dataset.panelContextAction === "clear-search") clearPanelSearch();
      if (btn.dataset.panelContextAction === "expand-all") expandAllPanels();
    });
  });
}

function clearPanelSearch() {
  const input = $("#panel-search-input");
  panelSearchQuery = "";
  if (input) input.value = "";
  applyPanelSearch();
}

function expandAllPanels() {
  const state = loadPanelState();
  document.querySelectorAll("[data-panel-section]").forEach((section) => {
    const id = section.dataset.panelSection;
    setPanelCollapsed(section, false);
    state[id] = false;
  });
  savePanelState(state);
  updatePanelContextNotice();
}

function buildSearchSnippet(text, query) {
  if (!text) return "仅标题匹配";
  const lower = text.toLowerCase();
  const idx = lower.indexOf(query);
  if (idx === -1) return text.slice(0, 28) + (text.length > 28 ? "…" : "");
  const start = Math.max(0, idx - 12);
  const end = Math.min(text.length, idx + query.length + 18);
  return `${start > 0 ? "…" : ""}${text.slice(start, end)}${end < text.length ? "…" : ""}`;
}

function renderPanelSearchResults(container, matches, query) {
  if (!container) return;
  container.classList.toggle("hidden", !query || matches.length === 0);
  if (!query || matches.length === 0) {
    container.innerHTML = "";
    return;
  }
  const ordered = matches.slice().sort((a, b) => Number(b.titleMatch) - Number(a.titleMatch));
  container.innerHTML = ordered.slice(0, 5).map((m) => `<button type="button" data-panel-search-result="${escapeAttr(m.id)}" data-test="panel-search-result-${escapeAttr(m.id)}">
    <span>${escapeHtml(m.title)}</span>
    <small>${escapeHtml(m.snippet)}</small>
  </button>`).join("");
  container.querySelectorAll("[data-panel-search-result]").forEach((btn) => {
    btn.addEventListener("click", () => focusPanelSection(btn.dataset.panelSearchResult));
  });
}

function focusPanelSection(id) {
  const section = document.querySelector(`[data-panel-section="${id}"]`);
  if (!section) return;
  sideNavScrollLockUntil = Date.now() + 700;
  const state = loadPanelState();
  setPanelCollapsed(section, false);
  state[id] = false;
  savePanelState(state);
  document.querySelectorAll("[data-panel-section].focused").forEach((el) => {
    el.classList.remove("focused");
  });
  section.classList.add("focused");
  setTimeout(() => section.classList.remove("focused"), 1600);
  section.scrollIntoView({ behavior: "smooth", block: "start" });
  setActiveSideNav(sideNavGroupForPanel(id));
}

function focusTimelineEvent(eventId) {
  if (!lastSidePanelState) return;
  activeTimelineFilter = "all";
  renderTimelinePanel(lastSidePanelState);
  focusPanelSection("timeline");
  const card = document.querySelector(`[data-event-id="${eventId}"]`);
  if (!card) return;
  document.querySelectorAll(".timeline-card.focused").forEach((el) => {
    el.classList.remove("focused");
  });
  card.classList.add("focused");
  setTimeout(() => card.classList.remove("focused"), 1600);
  card.scrollIntoView({ behavior: "smooth", block: "center" });
}

function clearPanelSearchHighlights(root) {
  root.querySelectorAll(`.${PANEL_SEARCH_HIGHLIGHT_CLASS}`).forEach((mark) => {
    mark.replaceWith(document.createTextNode(mark.textContent));
  });
  root.normalize();
}

function highlightPanelSearchMatches(root, query) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (!node.nodeValue.toLowerCase().includes(query)) return NodeFilter.FILTER_REJECT;
      if (node.parentElement.closest(`.${PANEL_SEARCH_HIGHLIGHT_CLASS}`)) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    },
  });
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  nodes.forEach((node) => highlightTextNode(node, query));
}

function highlightTextNode(node, query) {
  const text = node.nodeValue;
  const lower = text.toLowerCase();
  const fragment = document.createDocumentFragment();
  let pos = 0;
  let idx = lower.indexOf(query);
  while (idx !== -1) {
    if (idx > pos) fragment.appendChild(document.createTextNode(text.slice(pos, idx)));
    const mark = document.createElement("mark");
    mark.className = PANEL_SEARCH_HIGHLIGHT_CLASS;
    mark.setAttribute("data-test", "panel-search-highlight");
    mark.textContent = text.slice(idx, idx + query.length);
    fragment.appendChild(mark);
    pos = idx + query.length;
    idx = lower.indexOf(query, pos);
  }
  if (pos < text.length) fragment.appendChild(document.createTextNode(text.slice(pos)));
  node.replaceWith(fragment);
}

function setSideNavBadge(id, text, urgent = false) {
  const badge = document.querySelector(`[data-side-nav-badge="${id}"]`);
  if (!badge) return;
  badge.textContent = text;
  badge.classList.toggle("urgent", urgent);
}

function countSuggestedActions(state) {
  const player = (state.entities || []).find((e) => e.id === "player");
  if (!player) return 0;
  const loc = (state.locations || []).find((l) => l.id === player.location);
  const nearby = (state.entities || [])
    .filter((e) => e.id !== "player" && e.location === player.location);
  const progress = (state.flags || {}).story_progress || {};
  const hasClues = Object.values(progress)
    .some((thread) => ((thread || {}).clues || []).length > 0);
  const advisorsHere = nearby.filter((e) => (e.attributes || {}).is_advisor === true);

  let count = 1; // 仔细观察始终可用
  if (nearby.length > 0) count += 1;
  if (advisorsHere.length > 0) count += 1;
  if (hasClues || (loc && Object.keys(loc.exits || {}).length > 0)) count += 1;
  return Math.min(count, 4);
}

function renderSideNavBadges(state) {
  const player = (state.entities || []).find((e) => e.id === "player");
  const nearbyCount = player
    ? (state.entities || []).filter((e) => e.id !== "player" && e.location === player.location).length
    : 0;
  const progress = (state.flags || {}).story_progress || {};
  const clueCount = Object.values(progress).reduce(
    (sum, thread) => sum + ((thread || {}).clues || []).length, 0);
  const eventCount = (state.events || []).length;
  const pressureEntries = Object.values((state.flags || {}).pressure_clocks || {});
  const hasUrgentPressure = pressureEntries.some((clock) => {
    const dangerAt = Math.max(clock.danger_at || 1, 1);
    return ((clock.value || 0) / dangerAt) >= 0.8;
  });

  setSideNavBadge("time", `${nearbyCount}人在场`, hasUrgentPressure);
  setSideNavBadge("suggestions", `${countSuggestedActions(state)}项`);
  setSideNavBadge("story", `${clueCount}线索`, clueCount > 0);
  const dialogueEvents = (state.events || []).filter((ev) => ev.type === "dialogue");
  const dialogueCount = dialogueEvents.length;
  const dialogueNpcs = new Set(dialogueEvents.map((ev) => ev.target).filter(Boolean)).size;
  if (dialogueCount > 0) setSideNavBadge("dialogue-history", `${dialogueNpcs}NPC${dialogueCount}次`);
  const questEntries = ((state.flags || {}).quest_log || {}).entries || [];
  const questActive = questEntries.filter((e) => e.status === "active").length;
  const questCompleted = questEntries.filter((e) => e.status === "completed").length;
  if (questEntries.length > 0) {
    setSideNavBadge("quest", `${questActive}进行${questCompleted}完`, questActive > 0);
  }
  const evoCount = ((state.flags || {}).evolution_registry || []).length;
  if (evoCount > 0) setSideNavBadge("evolutions", `${evoCount}演化`);
  setSideNavBadge("review", `${eventCount}回合`);
}

function renderSidePanel(state) {
  lastSidePanelState = state;
  renderSideNavBadges(state);
  const t = state.time || {};
  const dayIndex = t.day_index !== undefined ? ` (第${t.day_index}天)` : "";
  $("#time-panel").textContent =
    `${t.year || ""} ${t.season || ""} ${t.time_of_day || ""}${dayIndex}`;

  renderWeatherPanel(state);
  renderSummaryPanel(state);
  renderPriorityPanel(state);
  renderRecentPanel(state);
  renderGapsPanel(state);

  const player = state.entities.find((e) => e.id === "player");
  if (player) {
    const a = player.attributes || {};
    const hp = a.hp ?? 0, maxHp = a.max_hp ?? 100;
    const pct = Math.max(0, Math.min(100, (hp / maxHp) * 100));
    const statuses = (player.status_effects || [])
      .map((s) => `<span class="status-tag">${s.name}</span>`)
      .join("");
    $("#player-panel").innerHTML = `
      <div class="row"><strong>${player.name}</strong>
        (${a.rank || "?"})</div>
      <div class="row">HP: ${hp}/${maxHp}
        <span class="hp-bar"><span style="width:${pct}%"></span></span>
      </div>
      <div class="row">钱: ${a.money_wen ?? 0} 文</div>
      <div class="row">位置: ${player.location} @[${(player.pos||[]).join(",")}]</div>
      <div class="row">状态: ${statuses || "<em>无</em>"}</div>
      <div class="row">物品: ${(player.inventory || [])
         .map((i) => i.name).join("、") || "<em>无</em>"}</div>
    `;
  }

  if (player) {
    const loc = state.locations.find((l) => l.id === player.location);
    if (loc) {
      const exits = Object.entries(loc.exits || {})
        .map(([dir, to]) => `${dir}→${to}`).join(", ") || "无";
      $("#location-panel").innerHTML = `
        <div class="row"><strong>${loc.name}</strong></div>
        <div class="row" style="font-size:.8em;color:#666">
          ${loc.description || ""}</div>
        <div class="row">出口: ${exits}</div>
      `;
    }

    const chain = buildSceneChain(state.locations, player.location);
    if (chain.length > 1) {
      const chainHtml = chain.map(([id, name], i) => {
        const isCurrent = id === player.location;
        const cls = isCurrent ? "chain-current" : "chain-other";
        return `<span class="${cls}">${name}</span>`;
      }).join('<span class="chain-arrow">→</span>');
      const chainEl = document.createElement("div");
      chainEl.className = "scene-chain";
      chainEl.setAttribute("data-test", "scene-chain");
      chainEl.innerHTML = chainHtml;
      const locPanel = document.getElementById("location-panel");
      locPanel.appendChild(chainEl);
    }
  }

  if (player) {
    const others = state.entities.filter(
      (e) => e.id !== "player" && e.location === player.location);
    if (others.length === 0) {
      $("#nearby-panel").innerHTML = "<em>无人</em>";
    } else {
      $("#nearby-panel").innerHTML = others.map((e) => {
        const a = e.attributes || {};
        const tags = (e.status_effects || [])
          .map((s) => `<span class="status-tag">${s.name}</span>`).join("");
        return `<div class="npc-row" data-test="npc-${e.id}">
          <span class="name">${e.name}</span>
          <span class="rank">[${a.rank || "?"}]</span>
          <br/>HP: ${a.hp ?? "?"} ${tags}
        </div>`;
      }).join("");
    }
  }

  renderRelationshipsPanel(state);
  renderSuggestionsPanel(state);
  renderTimelinePanel(state);
  renderPartyPanel(state);
  renderAdvisorPanel(state);
  renderObservationPanel(state);
  renderDialoguePanel(state);
  renderDialogueHistoryPanel(state);
  renderStoryPanel(state);
  renderCluesPanel(state);
  renderQuestLogPanel(state);
  renderPressurePanel(state);
  renderEndingPanel(state);
  renderSkillsPanel(state);
  renderEvolutionsPanel(state);
  renderReviewPanel(state);
  updateCollapsedPanelBadges();
  applyPanelSearch();
}

function renderWeatherPanel(state) {
  const weather = (state.flags || {}).weather;
  const panel = $("#weather-panel");
  if (!panel) return;
  if (!weather) {
    panel.innerHTML = "<em>天气未知</em>";
    return;
  }
  const conditionLabels = {
    clear: "晴", cloudy: "阴", rain: "雨",
    storm: "暴风雨", fog: "雾", snow: "雪",
  };
  const conditionIcons = {
    clear: "☀", cloudy: "☁", rain: "🌧",
    storm: "⛈", fog: "🌫", snow: "❄",
  };
  const intensityLabels = { light: "轻微", moderate: "中等", heavy: "强烈" };
  const condition = weather.condition || "clear";
  const intensity = weather.intensity || "light";
  const icon = conditionIcons[condition] || "☀";
  const label = conditionLabels[condition] || condition;
  const intensityLabel = intensityLabels[intensity] || intensity;
  panel.innerHTML = `
    <div class="weather-main">
      <span class="weather-icon">${icon}</span>
      <span class="weather-label">${label}</span>
      <span class="weather-intensity">${intensityLabel}</span>
    </div>
    ${weather.text ? `<div class="weather-text">${weather.text}</div>` : ""}
  `;
}

function renderSummaryPanel(state) {
  const player = (state.entities || []).find((e) => e.id === "player");
  if (!player) {
    $("#summary-panel").innerHTML = "<em>暂无</em>";
    return;
  }

  const loc = (state.locations || []).find((l) => l.id === player.location);
  const nearbyCount = (state.entities || [])
    .filter((e) => e.id !== "player" && e.location === player.location).length;
  const flags = state.flags || {};
  const progress = flags.story_progress || {};
  const clueCount = Object.values(progress).reduce(
    (sum, thread) => sum + ((thread || {}).clues || []).length, 0);
  const pressureEntries = Object.entries(flags.pressure_clocks || {});
  const topPressure = pressureEntries
    .map(([id, data]) => ({ id, value: data.value || 0, dangerAt: data.danger_at || 1 }))
    .sort((a, b) => (b.value / Math.max(b.dangerAt, 1)) - (a.value / Math.max(a.dangerAt, 1)))[0];
  const latestEvent = (state.events || [])[state.events.length - 1];
  const party = flags.party || { active_actor_id: "player" };
  const activeActor = (state.entities || []).find((e) => e.id === (party.active_actor_id || "player"));

  const pressureText = topPressure
    ? `${escapeHtml(topPressure.id)} ${topPressure.value}/${topPressure.dangerAt}`
    : "暂无";
  const eventText = latestEvent
    ? escapeHtml(latestEvent.summary || latestEvent.action_type || latestEvent.type || "未命名事件")
    : "暂无";

  const detailLines = isCompactDensity() ? "" : `
    <div class="summary-line">行动角色: ${escapeHtml(activeActor ? activeActor.name : party.active_actor_id || "player")}</div>
    <div class="summary-line latest">最新: ${eventText}</div>`;

  $("#summary-panel").innerHTML = `
    <div class="summary-grid">
      <div class="summary-item"><span class="summary-label">所在</span><span class="summary-value">${escapeHtml(loc ? loc.name : player.location)}</span></div>
      <div class="summary-item"><span class="summary-label">在场</span><span class="summary-value">${nearbyCount} 人</span></div>
      <div class="summary-item"><span class="summary-label">线索</span><span class="summary-value">${clueCount} 条</span></div>
      <div class="summary-item"><span class="summary-label">压力</span><span class="summary-value">${pressureText}</span></div>
    </div>
    ${detailLines}
  `;
}

function renderPriorityPanel(state) {
  const panel = $("#priority-panel");
  if (!panel) return;

  const flags = state.flags || {};
  const items = [];
  const pressure = Object.entries(flags.pressure_clocks || {})
    .map(([id, data]) => {
      const dangerAt = Math.max(data.danger_at || 1, 1);
      const value = data.value || 0;
      return { id, value, dangerAt, ratio: value / dangerAt };
    })
    .sort((a, b) => b.ratio - a.ratio)[0];
  if (pressure && pressure.ratio >= 0.5) {
    items.push({
      kind: pressure.ratio >= 0.8 ? "danger" : "warn",
      title: "压力接近危险线",
      body: `${pressure.id} ${pressure.value}/${pressure.dangerAt}`,
    });
  }

  const latestClue = latestStoryClue(flags.story_progress || {});
  if (latestClue) {
    items.push({
      kind: "clue",
      title: "最新线索",
      body: latestClue.clue || "未命名线索",
    });
  }

  const latestEvent = (state.events || [])[state.events.length - 1];
  if (latestEvent) {
    items.push({
      kind: "event",
      title: "最新事件",
      body: latestEvent.summary || latestEvent.action_type || latestEvent.type || "未命名事件",
    });
  }

  const suggestion = firstActionSuggestion(state);
  if (suggestion) {
    items.push({
      kind: "suggestion",
      title: "建议",
      body: suggestion,
    });
  }

  const limit = isCompactDensity() ? 2 : 4;
  panel.innerHTML = items.length
    ? items.slice(0, limit).map((item) => `<div class="priority-card ${item.kind}">
        <div class="priority-title">${escapeHtml(item.title)}</div>
        <div class="priority-body">${escapeHtml(item.body)}</div>
      </div>`).join("")
    : "<em>暂无紧要事项</em>";
}

function latestStoryClue(progress) {
  let latest = null;
  Object.values(progress || {}).forEach((thread) => {
    ((thread || {}).clues || []).forEach((clue) => { latest = clue; });
  });
  return latest;
}

function renderRecentPanel(state) {
  const panel = $("#recent-panel");
  if (!panel) return;
  const flags = state.flags || {};
  const items = [];
  const latestEvent = (state.events || [])[state.events.length - 1];
  if (latestEvent) {
    items.push({
      label: "事件",
      text: latestEvent.summary || latestEvent.action_type || latestEvent.type || "未命名事件",
      meta: latestEvent.turn !== undefined ? `回合 ${latestEvent.turn}` : "最近记录",
    });
  }
  const latestClue = latestStoryClue(flags.story_progress || {});
  if (latestClue) {
    items.push({
      label: "线索",
      text: latestClue.clue || "未命名线索",
      meta: [latestClue.source_entity, latestClue.location_id].filter(Boolean).join(" · ") || "新线索",
    });
  }
  const topPressure = Object.entries(flags.pressure_clocks || {})
    .map(([id, data]) => ({ id, value: data.value || 0, dangerAt: data.danger_at || 1 }))
    .sort((a, b) => (b.value / Math.max(b.dangerAt, 1)) - (a.value / Math.max(a.dangerAt, 1)))[0];
  if (topPressure) {
    items.push({
      label: "压力",
      text: `${topPressure.id} ${topPressure.value}/${topPressure.dangerAt}`,
      meta: (topPressure.value / Math.max(topPressure.dangerAt, 1)) >= 0.8 ? "接近危险线" : "持续变化",
    });
  }
  panel.innerHTML = items.length
    ? items.map((item) => `<div class="recent-card" data-test="recent-${escapeAttr(item.label)}">
        <span class="recent-label">${escapeHtml(item.label)}</span>
        <strong>${escapeHtml(item.text)}</strong>
        <em>${escapeHtml(item.meta)}</em>
      </div>`).join("")
    : "<em>暂无变化</em>";
}

function renderGapsPanel(state) {
  const panel = $("#gaps-panel");
  if (!panel) return;
  const flags = state.flags || {};
  const progress = flags.story_progress || {};
  const seeds = flags.story_seeds || {};
  const player = (state.entities || []).find((e) => e.id === "player");
  const gaps = [];

  const storyThreads = [];
  if (seeds.main_thread) {
    storyThreads.push({ id: "main_thread", title: seeds.main_thread.title || "主线" });
  }
  (seeds.side_threads || []).forEach((thread) => {
    storyThreads.push({ id: thread.id, title: thread.title || thread.id });
  });
  const unopenedThreads = storyThreads.filter((thread) => ((progress[thread.id] || {}).clues || []).length === 0);
  if (unopenedThreads.length > 0) {
    gaps.push({
      kind: "story",
      title: "未触发剧情线程",
      body: unopenedThreads.slice(0, 3).map((thread) => thread.title).join("、"),
      meta: `${unopenedThreads.length}/${storyThreads.length} 条暂无线索`,
    });
  }

  if (player) {
    const observations = ((flags.observations || {}).player) || {};
    const seenKeys = new Set(Object.keys(observations));
    const loc = (state.locations || []).find((l) => l.id === player.location);
    const hiddenDetails = [];
    function collectHiddenDetails(target, targetType) {
      const source = targetType === "entity"
        ? ((target.attributes || {}).observable_details || [])
        : (target.observable_details || []);
      source.forEach((detail) => {
        const key = `${targetType}:${target.id}:${detail.id}`;
        if (!seenKeys.has(key) && (detail.discovery_value || 0) > ((player.attributes || {}).observation || 10)) {
          hiddenDetails.push(target.name || target.id);
        }
      });
    }
    if (loc) collectHiddenDetails(loc, "location");
    (state.entities || [])
      .filter((e) => e.id !== "player" && e.location === player.location)
      .forEach((e) => collectHiddenDetails(e, "entity"));
    if (hiddenDetails.length > 0) {
      gaps.push({
        kind: "observation",
        title: "可能遗漏细节",
        body: Array.from(new Set(hiddenDetails)).slice(0, 3).join("、"),
        meta: `${hiddenDetails.length} 个高难度观察点`,
      });
    }

    const nearbyAdvisors = (state.entities || [])
      .filter((e) => e.id !== "player" && e.location === player.location && (e.attributes || {}).is_advisor === true);
    const unconsulted = nearbyAdvisors.filter((advisor) =>
      !((advisor.attributes || {}).memories || []).some((memory) =>
        ((memory.text || memory.summary || "").includes("请教"))
      )
    );
    if (unconsulted.length > 0) {
      gaps.push({
        kind: "advisor",
        title: "附近顾问尚未请教",
        body: unconsulted.map((advisor) => advisor.name).join("、"),
        meta: "可直接从顾问面板发起请教",
      });
    }
  }

  const limit = isCompactDensity() ? 2 : 4;
  panel.innerHTML = gaps.length
    ? gaps.slice(0, limit).map((gap) => `<div class="gap-card ${gap.kind}" data-test="gap-${gap.kind}">
        <div class="gap-title">${escapeHtml(gap.title)}</div>
        <div class="gap-body">${escapeHtml(gap.body)}</div>
        <div class="gap-meta">${escapeHtml(gap.meta)}</div>
      </div>`).join("")
    : "<em>暂无明显信息缺口</em>";
}

function firstActionSuggestion(state) {
  const player = (state.entities || []).find((e) => e.id === "player");
  if (!player) return null;
  const progress = (state.flags || {}).story_progress || {};
  const hasClues = Object.values(progress)
    .some((thread) => ((thread || {}).clues || []).length > 0);
  if (hasClues) return "梳理线索";
  const nearby = (state.entities || [])
    .filter((e) => e.id !== "player" && e.location === player.location);
  const advisorsHere = nearby.filter((e) => (e.attributes || {}).is_advisor === true);
  if (advisorsHere.length > 0) return `请教${advisorsHere[0].name}`;
  if (nearby.length > 0) return `询问${nearby[0].name}`;
  return "仔细观察";
}

function renderRelationshipsPanel(state) {
  const player = (state.entities || []).find((e) => e.id === "player");
  const panel = $("#relationships-panel");
  if (!panel || !player) return;

  const allNpcs = (state.entities || []).filter((e) => e.id !== "player");
  const nearby = allNpcs.filter((e) => e.location === player.location);
  const historical = allNpcs.filter((e) =>
    e.location !== player.location && (e.attributes?.memories?.length || 0) > 0
  );

  if (nearby.length === 0 && historical.length === 0) {
    panel.innerHTML = "<em>附近暂无可观察关系</em>";
    return;
  }

  function renderCard(e, isHistorical) {
    const attrs = e.attributes || {};
    const memories = attrs.memories || [];
    const latestMemory = memories[memories.length - 1];
    const memoryText = latestMemory
      ? (latestMemory.text || latestMemory.summary || JSON.stringify(latestMemory))
      : "尚无互动记忆";
    const importance = latestMemory && latestMemory.importance !== undefined
      ? `重要度 ${latestMemory.importance}`
      : "无记录";
    const role = attrs.occupation || attrs.rank || "身份不明";
    const tone = attrs.personality || "态度未明";
    const locationHint = isHistorical ? `<div class="relationship-location">当前在: ${escapeHtml(findLocationName(state, e.location) || "未知")}</div>` : "";
    return `<div class="relationship-card${isHistorical ? " relationship-historical" : ""}" data-test="relationship-${e.id}">
      <div class="relationship-header">
        <span class="relationship-name">${escapeHtml(e.name)}</span>
        <span class="relationship-role">${escapeHtml(role)}</span>
      </div>
      <div class="relationship-tone">态度线索: ${escapeHtml(tone)}</div>
      ${isCompactDensity() ? "" : `<div class="relationship-memory">最近记忆: ${escapeHtml(memoryText)}</div>`}
      ${locationHint}
      <div class="relationship-meta">记忆 ${memories.length} 条 · ${escapeHtml(importance)}</div>
    </div>`;
  }

  let html = "";
  if (nearby.length > 0) {
    const visibleNearby = isCompactDensity() ? nearby.slice(0, 2) : nearby;
    html += visibleNearby.map((e) => renderCard(e, false)).join("");
    if (isCompactDensity() && nearby.length > visibleNearby.length) {
      html += `<div class="compact-more">另有 ${nearby.length - visibleNearby.length} 人，切换详细查看</div>`;
    }
  }

  if (historical.length > 0) {
    if (nearby.length > 0) {
      html += `<div class="relationship-divider"><span>曾互动</span></div>`;
    }
    const visibleHistorical = isCompactDensity() ? historical.slice(0, 2) : historical;
    html += visibleHistorical.map((e) => renderCard(e, true)).join("");
    if (isCompactDensity() && historical.length > visibleHistorical.length) {
      html += `<div class="compact-more">另有 ${historical.length - visibleHistorical.length} 人，切换详细查看</div>`;
    }
  }

  panel.innerHTML = html;
}

function buildSceneChain(locations, currentId) {
  const byId = {};
  locations.forEach((l) => { byId[l.id] = l; });

  let left = currentId;
  const visited = new Set();
  while (true) {
    const loc = byId[left];
    if (!loc) break;
    visited.add(left);
    let found = false;
    for (const [dir, target] of Object.entries(loc.exits || {})) {
      if (!visited.has(target) && byId[target]) {
        left = target;
        found = true;
        break;
      }
    }
    if (!found) break;
  }

  const chain = [];
  let cur = left;
  const visited2 = new Set();
  while (cur && byId[cur] && !visited2.has(cur)) {
    const loc = byId[cur];
    visited2.add(cur);
    chain.push([cur, loc.name]);
    let next = null;
    for (const [dir, target] of Object.entries(loc.exits || {})) {
      if (!visited2.has(target) && byId[target]) {
        next = target;
        break;
      }
    }
    cur = next;
  }
  return chain;
}

// ===================================================================
// Action suggestions panel (Phase 7 polish)
// ===================================================================
function renderSuggestionsPanel(state) {
  const player = (state.entities || []).find((e) => e.id === "player");
  if (!player) {
    $("#suggestions-panel").innerHTML = "<em>暂无</em>";
    return;
  }

  const loc = (state.locations || []).find((l) => l.id === player.location);
  const nearby = (state.entities || [])
    .filter((e) => e.id !== "player" && e.location === player.location);
  const flags = state.flags || {};
  const progress = flags.story_progress || {};
  const hasClues = Object.values(progress)
    .some((thread) => ((thread || {}).clues || []).length > 0);
  const observations = ((flags.observations || {}).player) || {};
  const hasObservations = Object.keys(observations).length > 0;
  const advisorsHere = nearby.filter((e) => (e.attributes || {}).is_advisor === true);

  const suggestions = [];
  suggestions.push({
    id: "observe",
    label: "仔细观察",
    text: "我仔细观察四周,留意可疑细节。",
    reason: hasObservations ? "继续核对已发现细节" : "先看清现场与人物",
  });

  if (nearby.length > 0) {
    suggestions.push({
      id: "talk",
      label: "询问在场者",
      text: `我上前询问${nearby[0].name}：此处刚才发生了什么？`,
      reason: `附近有${nearby.length}人在场`,
    });
  }

  if (advisorsHere.length > 0) {
    suggestions.push({
      id: "advisor",
      label: "请教顾问",
      text: `向顾问${advisorsHere[0].name}(${advisorsHere[0].id})请教：我现在该怎么办？请结合当前处境给我一两条可行建议。`,
      reason: `${advisorsHere[0].name}就在附近`,
    });
  }

  if (hasClues) {
    suggestions.push({
      id: "clues",
      label: "梳理线索",
      text: "我停下来梳理已掌握的线索,判断下一步该找谁或去哪。",
      reason: "已有线索可复盘",
    });
  } else if (loc && Object.keys(loc.exits || {}).length > 0) {
    const [dir, target] = Object.entries(loc.exits)[0];
    suggestions.push({
      id: "move",
      label: "查看出口",
      text: `我查看${dir}面的去路,准备前往${target}。`,
      reason: "当前位置有可探索出口",
    });
  }

  const limit = isCompactDensity() ? 2 : 4;
  const panel = $("#suggestions-panel");
  panel.innerHTML = suggestions.slice(0, limit).map((s) =>
    `<button class="suggestion-card" data-test="suggestion-${s.id}" data-action="${escapeAttr(s.text)}">
      <span class="suggestion-title">${escapeHtml(s.label)}</span>
      ${isCompactDensity() ? "" : `<span class="suggestion-reason">${escapeHtml(s.reason)}</span>`}
    </button>`
  ).join("") || "<em>暂无</em>";
  panel.querySelectorAll(".suggestion-card").forEach((btn) => {
    btn.addEventListener("click", () => handleTurn(btn.dataset.action));
  });
}

// ===================================================================
// Timeline panel (Phase 7 polish)
// ===================================================================
let activeTimelineFilter = "all";
const EVENT_TYPE_ORDER = ["plot", "social", "combat", "trade", "test"];
const EVENT_TYPE_FILTERS = ["all", ...EVENT_TYPE_ORDER];
const EVENT_TYPE_LABELS = {
  all: "全部",
  plot: "剧情",
  social: "社交",
  combat: "战斗",
  trade: "交易",
  test: "其他",
};
const EVENT_TYPE_STYLES = {
  combat: "type-combat",
  social: "type-social",
  trade: "type-trade",
  plot: "type-plot",
  test: "type-test",
};
const TIMELINE_TYPE_DESCRIPTIONS = {
  plot: "线索、结局与主线推进",
  social: "请教、交谈与人物互动",
  combat: "攻击、受伤与战斗后果",
  trade: "买卖、雇佣与钱物变化",
  test: "移动、观察及未归类记录",
};
const TIMELINE_LEGEND_HTML = `<div class="timeline-legend" data-test="timeline-legend">
  ${EVENT_TYPE_ORDER.map((type) =>
    `<span><i class="timeline-legend-dot type-${type}"></i><strong>${EVENT_TYPE_LABELS[type]}</strong>${TIMELINE_TYPE_DESCRIPTIONS[type]}</span>`
  ).join("")}
</div>`;

function renderTimelinePanel(state) {
  const maxEvents = isCompactDensity() ? 4 : 8;
  const events = (state.events || []).slice(-maxEvents).reverse();
  const panel = $("#timeline-panel");
  if (events.length === 0) {
    panel.innerHTML = "<em>暂无</em>";
    return;
  }

  const typedEvents = events.map((ev) => ({ ...ev, eventType: detectTimelineType(ev) }));
  const counts = typedEvents.reduce((acc, ev) => {
    acc[ev.eventType] = (acc[ev.eventType] || 0) + 1;
    return acc;
  }, { all: typedEvents.length });
  const availableTypes = new Set(typedEvents.map((ev) => ev.eventType));
  if (activeTimelineFilter !== "all" && !availableTypes.has(activeTimelineFilter)) {
    activeTimelineFilter = "all";
  }
  const visibleEvents = activeTimelineFilter === "all"
    ? typedEvents
    : typedEvents.filter((ev) => ev.eventType === activeTimelineFilter);

  const filterHtml = `<div class="timeline-filters" data-test="timeline-filters">${EVENT_TYPE_FILTERS.map((type) => {
    const count = counts[type] || 0;
    const disabled = type !== "all" && count === 0;
    return `<button type="button" class="timeline-filter ${activeTimelineFilter === type ? 'active' : ''}" data-test="timeline-filter-${type}" data-timeline-filter="${type}" ${disabled ? 'disabled' : ''}>${EVENT_TYPE_LABELS[type]} ${count}</button>`;
  }).join("")}</div>`;
  const summaryHtml = renderTimelineSummary(counts, activeTimelineFilter);

  const eventCount = visibleEvents.length;
  const eventHtml = visibleEvents.length
    ? renderTimelineGroups(visibleEvents, eventCount)
    : "<em>当前筛选下暂无事件</em>";

  panel.innerHTML = summaryHtml + TIMELINE_LEGEND_HTML + filterHtml + eventHtml;
  panel.querySelectorAll("[data-timeline-filter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      activeTimelineFilter = btn.dataset.timelineFilter || "all";
      renderTimelinePanel(state);
    });
  });
}

function renderTimelineGroups(events, eventCount) {
  const groupSummaries = summarizeTimelineGroups(events);
  let lastGroup = "";
  return events.map((ev, i) => {
    const summary = ev.summary || ev.action_type || ev.type || "未命名事件";
    const actor = ev.actor ? `<span class="timeline-actor">${escapeHtml(ev.actor)}</span>` : "";
    const turn = ev.turn !== undefined ? `回合 ${ev.turn}` : `事件 ${ev.id || ""}`;
    const timestamp = ev.timestamp ? ` · ${escapeHtml(ev.timestamp)}` : "";
    const etype = ev.eventType;
    const typeBadge = `<span class="timeline-type ${EVENT_TYPE_STYLES[etype] || EVENT_TYPE_STYLES.test}">${etype}</span>`;
    const isNewest = i === 0 && eventCount > 0 ? '<span class="timeline-newest">最新</span>' : "";
    const group = timelineEventGroup(ev);
    const groupHeader = group !== lastGroup
      ? `<div class="timeline-group" data-test="timeline-group"><span>${escapeHtml(group)}</span><small data-test="timeline-group-summary">${escapeHtml(groupSummaries[group] || "")}</small></div>`
      : "";
    lastGroup = group;
    return `${groupHeader}<div class="timeline-card" data-test="timeline-event-${ev.id || 'unknown'}" data-event-id="${escapeAttr(ev.id || 'unknown')}" data-event-type="${escapeHtml(etype)}">
      <div class="timeline-meta">${typeBadge}${isNewest}${escapeHtml(turn)}${timestamp}</div>
      <div class="timeline-summary">${actor}${escapeHtml(summary)}</div>
    </div>`;
  }).join("");
}

function summarizeTimelineGroups(events) {
  const counts = events.reduce((acc, ev) => {
    const group = timelineEventGroup(ev);
    if (!acc[group]) acc[group] = { total: 0 };
    acc[group].total += 1;
    acc[group][ev.eventType] = (acc[group][ev.eventType] || 0) + 1;
    return acc;
  }, {});
  return Object.fromEntries(Object.entries(counts).map(([group, data]) => {
    const parts = EVENT_TYPE_ORDER
      .filter((type) => data[type] > 0)
      .map((type) => `${EVENT_TYPE_LABELS[type]}${data[type]}`);
    return [group, `${data.total}件 · ${parts.join(" / ")}`];
  }));
}

function timelineEventGroup(ev) {
  if (ev.turn !== undefined && ev.turn !== null) return `回合 ${ev.turn}`;
  if (ev.timestamp) return ev.timestamp;
  return "未分组事件";
}

function renderTimelineSummary(counts, activeFilter) {
  const activeCount = counts[activeFilter] || 0;
  const total = counts.all || 0;
  const dominantType = EVENT_TYPE_ORDER
    .filter((type) => (counts[type] || 0) > 0)
    .sort((a, b) => (counts[b] || 0) - (counts[a] || 0))[0];
  const dominantText = dominantType
    ? `${EVENT_TYPE_LABELS[dominantType]}最多(${counts[dominantType]}件)`
    : "暂无类型";
  const activeText = activeFilter === "all"
    ? `显示全部 ${total} 件`
    : `显示${EVENT_TYPE_LABELS[activeFilter]} ${activeCount} 件`;
  return `<div class="timeline-summary-box" data-test="timeline-summary">
    <span>${activeText}</span>
    <span>${dominantText}</span>
  </div>`;
}

function detectTimelineType(ev) {
  const et = (ev.type || "").toLowerCase();
  const at = (ev.action_type || "").toLowerCase();
  const s = (ev.summary || "").toLowerCase();
  const combined = `${et} ${at} ${s}`;
  if (/战斗|combat|damage|attack|受伤/.test(combined)) return "combat";
  if (/交易|trade|purchase|买卖/.test(combined)) return "trade";
  if (/社交|social|请教|闲谈/.test(combined)) return "social";
  if (/剧情|plot|clue|线索|结局|ending/.test(combined)) return "plot";
  return "test";
}

// ===================================================================
// Party panel (Phase 6 Step 4)
// ===================================================================
function renderPartyPanel(state) {
  const player = (state.entities || []).find((e) => e.id === "player");
  if (!player) {
    $("#party-panel").innerHTML = renderEmptyGuide("👥", "暂无队伍", [
      { label: "邀请 NPC 同行", hint: "组建冒险队伍" },
      { label: "与 NPC 建立关系", hint: "提升好感度" },
    ]);
    return;
  }

  const party = (state.flags || {}).party || {
    leader_id: "player",
    active_actor_id: "player",
    members: [{ entity_id: "player", role: "主角", joined_reason: "初始队伍" }],
  };
  const members = (party.members || [])
    .map((m) => {
      const entity = (state.entities || []).find((e) => e.id === m.entity_id);
      return entity ? { ...m, entity } : null;
    })
    .filter(Boolean);

  if (members.length === 0) {
    $("#party-panel").innerHTML = renderEmptyGuide("👥", "队伍为空", [
      { label: "邀请 NPC 同行", action: "我想邀请在场的人与我同行。", hint: "组建冒险队伍" },
      { label: "探索不同地点", hint: "结识更多伙伴" },
    ]);
    return;
  }

  $("#party-panel").innerHTML = members.map((m) => {
    const e = m.entity;
    const a = e.attributes || {};
    const active = e.id === (party.active_actor_id || "player");
    const loc = (state.locations || []).find((l) => l.id === e.location);
    const locName = loc ? loc.name : e.location;
    return `<div class="party-card ${active ? 'active' : ''}" data-test="party-${e.id}">
      <div class="party-name">${escapeHtml(e.name)}${active ? ' <span class="party-active">行动中</span>' : ''}</div>
      <div class="party-role">${escapeHtml(m.role || a.occupation || a.rank || '')}</div>
      <div class="party-loc">位置: ${escapeHtml(locName || '')}</div>
      ${e.id !== "player"
        ? `<button class="party-action" data-test="set-active-${e.id}"
            onclick="handleTurn('让${escapeHtml(e.name)}作为当前行动角色,由他来出面处理下一步。')">让其行动</button>`
        : ''}
    </div>`;
  }).join("");
}

// ===================================================================
// Advisor panel (Phase 6 Step 2)
// ===================================================================
function renderAdvisorPanel(state) {
  const advisors = (state.entities || []).filter(
    (e) => e.type !== "player" && (e.attributes || {}).is_advisor === true
  );
  if (advisors.length === 0) {
    $("#advisor-panel").innerHTML = renderEmptyGuide("💬", "暂无顾问", [
      { label: "与 NPC 交谈", hint: "寻找可提供建议的人" },
      { label: "探索不同地点", hint: "结识更多人物" },
    ]);
    return;
  }

  // Prefer advisors at player's current location
  const player = state.entities.find((e) => e.id === "player");
  const nearby = player
    ? advisors.filter((a) => a.location === player.location)
    : [];
  const others = player
    ? advisors.filter((a) => a.location !== player.location)
    : [];

  let html = "";

  function card(advisor) {
    const a = advisor.attributes || {};
    const topics = (a.advisor_topics || [])
      .map((t) => `<span class="advisor-topic">${escapeHtml(t)}</span>`)
      .join("");
    const isNearby = player && advisor.location === player.location;
    const locName = (state.locations || []).find(
      (l) => l.id === advisor.location
    );
    const locLabel = locName ? locName.name : advisor.location;
    return `<div class="advisor-card" data-test="advisor-${advisor.id}">
      <div class="advisor-name">${escapeHtml(advisor.name)}</div>
      <div class="advisor-role">${escapeHtml(a.occupation || a.rank || "")}</div>
      ${topics ? `<div class="advisor-topics">${topics}</div>` : ""}
      <div class="advisor-loc">位置: ${escapeHtml(locLabel)}</div>
      ${isNearby
        ? `<button class="advisor-ask" data-test="ask-advisor-${advisor.id}"
            onclick="handleTurn('向顾问${escapeHtml(advisor.name)}(${advisor.id})请教：我现在该怎么办？请结合当前处境给我一两条可行建议。')">
            请教</button>`
        : `<span class="advisor-far">前往请教</span>`}
    </div>`;
  }

  nearby.forEach((a) => { html += card(a); });
  others.forEach((a) => { html += card(a); });

  $("#advisor-panel").innerHTML = html || "<em>暂无</em>";
}

// ===================================================================
// Observation panel (Phase 6 Step 3)
// ===================================================================
function renderObservationPanel(state) {
  const player = (state.entities || []).find((e) => e.id === "player");
  if (!player) {
    $("#observation-panel").innerHTML = renderEmptyGuide("👁", "尚无观察记录", [
      { label: "仔细观察四周", action: "我仔细观察四周,留意可疑细节。", hint: "发现隐藏细节" },
      { label: "与 NPC 交谈", hint: "了解人物背景" },
    ]);
    return;
  }

  const observations = (((state.flags || {}).observations || {}).player) || {};
  const seenKeys = new Set(Object.keys(observations));
  const details = [];
  const loc = (state.locations || []).find((l) => l.id === player.location);

  function addDetails(target, targetType) {
    const source = targetType === "entity"
      ? ((target.attributes || {}).observable_details || [])
      : (target.observable_details || []);
    source.forEach((d) => {
      const key = `${targetType}:${target.id}:${d.id}`;
      if ((d.discovery_value || 0) <= ((player.attributes || {}).observation || 10) || seenKeys.has(key)) {
        details.push({ ...d, target_id: target.id, target_name: target.name, target_type: targetType, discovered: seenKeys.has(key) });
      }
    });
  }

  if (loc) addDetails(loc, "location");
  (state.entities || [])
    .filter((e) => e.id !== "player" && e.location === player.location)
    .forEach((e) => addDetails(e, "entity"));

  let html = `<button class="observe-btn" data-test="observe-button" onclick="handleTurn('我仔细观察四周,留意可疑细节。')">仔细观察</button>`;
  if (details.length === 0) {
    html += "<em>尚无可见细节</em>";
  } else {
    html += details.map((d) => {
      const discoveryValue = d.discovery_value || 0;
      let difficultyClass = "easy";
      let difficultyLabel = "简单";
      if (discoveryValue >= 15) {
        difficultyClass = "hard";
        difficultyLabel = "困难";
      } else if (discoveryValue >= 10) {
        difficultyClass = "medium";
        difficultyLabel = "中等";
      }
      return `<div class="observation-card ${d.discovered ? 'discovered' : ''}" data-test="observation-${d.id}">
        <div class="observation-header">
          <div class="observation-target">${escapeHtml(d.target_name || d.target_id)}</div>
          <div class="observation-difficulty ${difficultyClass}" title="发现值: ${discoveryValue}">${difficultyLabel}</div>
        </div>
        <div class="observation-text">${escapeHtml(d.text || '')}</div>
        ${d.discovered ? '<div class="observation-mark">已发现</div>' : ''}
      </div>`;
    }).join("");
  }
  $("#observation-panel").innerHTML = html;
}

// ===================================================================
// Dialogue panel (Phase 28)
// ===================================================================
function renderDialoguePanel(state) {
  const player = (state.entities || []).find((e) => e.id === "player");
  if (!player) {
    $("#dialogue-panel").innerHTML = renderEmptyGuide("💬", "暂无可对话 NPC", [
      { label: "探索不同地点", hint: "遇到更多人物" },
    ]);
    return;
  }

  const nearby = (state.entities || []).filter(
    (e) => e.type === "npc" && e.location === player.location
  );

  if (nearby.length === 0) {
    $("#dialogue-panel").innerHTML = "<em>附近无人</em>";
    return;
  }

  let html = "";
  for (const npc of nearby) {
    const dl = (npc.attributes || {}).dialogue_lines;
    if (!dl) continue;

    const attitudes = (npc.attributes || {}).attitude || {};
    const att = attitudes[player.id] || 0;
    const attLabel = att >= 30 ? "友善" : att >= 10 ? "中立" : att >= -10 ? "陌生" : att >= -30 ? "冷淡" : "敌意";
    const attCls = att >= 10 ? "att-positive" : att <= -10 ? "att-negative" : "att-neutral";

    const greetings = (dl.greetings || []).length;
    const topics = (dl.topics || []).length;
    const farewells = (dl.farewells || []).length;

    // Count available topics at current attitude
    let availTopics = 0;
    for (const t of (dl.topics || [])) {
      if (att >= (t.unlock_attitude || -100)) availTopics++;
    }

    html += `<div class="dialogue-npc" data-test="dialogue-${npc.id}">
      <div class="dialogue-header">
        <span class="dialogue-name">${escapeHtml(npc.name)}</span>
        <span class="dialogue-attitude ${attCls}">${attLabel} (${att})</span>
      </div>
      <div class="dialogue-stats">
        <span>问候 ${greetings}</span>
        <span>话题 ${availTopics}/${topics}</span>
        <span>告别 ${farewells}</span>
      </div>`;

    // Show first meeting specials
    const specials = (dl.special || []).filter((s) => {
      if (s.trigger === "first_meeting") {
        const mems = (npc.attributes || {}).memories || [];
        return !mems.some((m) => (m.text || "").includes("玩家") || (m.text || "").includes(player.id));
      }
      if (s.trigger === "high_attitude") return att >= (s.min_attitude || 50);
      if (s.trigger === "low_attitude") return att <= (s.max_attitude || -20);
      return true;
    });
    if (specials.length > 0) {
      html += `<div class="dialogue-specials">
        ${specials.map((s) => `<div class="dialogue-special">✨ ${escapeHtml(s.text)}</div>`).join("")}
      </div>`;
    }

    html += `<button class="dialogue-btn" data-test="talk-${npc.id}"
      onclick="handleTurn('我上前与${escapeHtml(npc.name)}攀谈。')">交谈</button>`;
    html += `</div>`;
  }

  $("#dialogue-panel").innerHTML = html || "<em>附近 NPC 无对话素材</em>";
}

// ===================================================================
// Dialogue History panel (Phase 30, enhanced Phase 34)
// ===================================================================
function renderAttitudeSparkline(history, att, large) {
  if (history.length < 2) return "";
  // Convert deltas to cumulative values
  const cumulative = [];
  let sum = 0;
  for (const d of history) { sum += d; cumulative.push(sum); }
  const w = large ? 120 : 40, h = large ? 32 : 14;
  const min = Math.min(...cumulative, 0);
  const max = Math.max(...cumulative, 1);
  const range = max - min || 1;
  const step = w / Math.max(cumulative.length - 1, 1);
  const pts = cumulative.map((v, i) =>
    `${(i * step).toFixed(1)},${(h - ((v - min) / range) * h).toFixed(1)}`
  ).join(" ");
  const color = att >= 10 ? "#6a9a2a" : att <= -10 ? "#c44" : "#888";
  // Dots on each data point when large
  const dots = large ? cumulative.map((v, i) =>
    `<circle cx="${(i * step).toFixed(1)}" cy="${(h - ((v - min) / range) * h).toFixed(1)}" r="2" fill="${color}"/>`
  ).join("") : "";
  const titleEl = large && cumulative.length > 0
    ? `<title>起点 ${cumulative[0]}, 最终 ${cumulative[cumulative.length - 1]}</title>`
    : "";
  return `<svg class="attitude-sparkline" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${titleEl}<polyline points="${pts}" fill="none" stroke="${color}" stroke-width="${large ? 2 : 1.5}" stroke-linecap="round" stroke-linejoin="round"/>${dots}</svg>`;
}

function renderDialogueHistoryPanel(state) {
  const events = (state.events || []).filter((ev) => ev.type === "dialogue");
  const panel = $("#dialogue-history-panel");

  if (events.length === 0) {
    panel.innerHTML = renderEmptyGuide("📜", "暂无对话记录", [
      { label: "与 NPC 交谈", hint: "积累对话历史" },
    ]);
    return;
  }

  // Build attitude history from events
  const attitudeHistory = {};
  const dialogueEvents = events.slice().reverse();

  for (const ev of dialogueEvents) {
    const npcId = ev.target;
    if (!npcId) continue;

    if (!attitudeHistory[npcId]) {
      attitudeHistory[npcId] = {
        npcName: ev.target_name || npcId,
        entries: [],
        currentAttitude: 0,
        deltas: [],
      };
    }

    const entry = {
      turn: ev.turn || 0,
      topic: ev.topic || "",
      playerLine: ev.player_line || "",
      npcResponse: ev.npc_response || "",
      attitudeDelta: ev.attitude_delta || 0,
    };

    attitudeHistory[npcId].entries.push(entry);
    attitudeHistory[npcId].currentAttitude += entry.attitudeDelta;
    attitudeHistory[npcId].deltas.push(entry.attitudeDelta);
  }

  // Collect filter data
  const npcIds = Object.keys(attitudeHistory);
  const allTopics = [...new Set(events.map((ev) => ev.topic).filter(Boolean))];

  // --- Phase 34: topic statistics ---
  const topicStats = {};
  for (const ev of events) {
    const t = ev.topic || "(无话题)";
    if (!topicStats[t]) topicStats[t] = 0;
    topicStats[t]++;
  }
  const sortedTopics = Object.entries(topicStats).sort((a, b) => b[1] - a[1]);

  // --- Phase 34: attitude distribution ---
  let friendlyCount = 0, neutralCount = 0, coldCount = 0;
  for (const data of Object.values(attitudeHistory)) {
    const a = data.currentAttitude;
    if (a >= 10) friendlyCount++;
    else if (a <= -10) coldCount++;
    else neutralCount++;
  }

  // Render summary
  const npcCount = npcIds.length;
  const totalDialogues = events.length;

  let html = `<div class="dialogue-history-summary" data-test="dialogue-history-summary">
    <div><span>对话总数</span><strong>${totalDialogues}</strong></div>
    <div><span>交谈 NPC</span><strong>${npcCount}</strong></div>
    ${allTopics.length > 0 ? `<div><span>话题数</span><strong>${allTopics.length}</strong></div>` : ""}
  </div>`;

  // --- Phase 34: attitude distribution bar ---
  if (npcCount > 1) {
    const total = friendlyCount + neutralCount + coldCount;
    html += `<div class="dialogue-history-att-dist" data-test="dialogue-history-att-dist">
      <div class="dialogue-history-att-dist-bar">
        ${friendlyCount > 0 ? `<span class="att-dist-friendly" style="width:${(friendlyCount / total * 100).toFixed(1)}%">友善 ${friendlyCount}</span>` : ""}
        ${neutralCount > 0 ? `<span class="att-dist-neutral" style="width:${(neutralCount / total * 100).toFixed(1)}%">中立 ${neutralCount}</span>` : ""}
        ${coldCount > 0 ? `<span class="att-dist-cold" style="width:${(coldCount / total * 100).toFixed(1)}%">冷淡 ${coldCount}</span>` : ""}
      </div>
    </div>`;
  }

  // --- Phase 34: topic statistics ---
  if (sortedTopics.length > 1) {
    const maxTopicCount = sortedTopics[0][1];
    html += `<div class="dialogue-history-topic-stats" data-test="dialogue-history-topic-stats">
      <div class="dialogue-history-topic-stats-title">话题分布</div>
      ${sortedTopics.slice(0, 5).map(([topic, count]) =>
        `<div class="dialogue-history-topic-bar-row">
          <span class="dialogue-history-topic-bar-label">${escapeHtml(topic)}</span>
          <div class="dialogue-history-topic-bar"><span style="width:${(count / maxTopicCount * 100).toFixed(1)}%"></span></div>
          <span class="dialogue-history-topic-bar-count">${count}</span>
        </div>`
      ).join("")}
    </div>`;
  }

  // Render NPC filter chips
  html += `<div class="dialogue-history-filters" data-test="dialogue-history-filters">
    <button type="button" class="quest-filter-chip active" data-dh-filter-type="npc" data-dh-filter-value="all">全部</button>
    ${npcIds.map((id) => `<button type="button" class="quest-filter-chip" data-dh-filter-type="npc" data-dh-filter-value="${escapeAttr(id)}">${escapeHtml(attitudeHistory[id].npcName)}</button>`).join("")}
  </div>`;

  // --- Phase 34: search input ---
  html += `<div class="dialogue-history-search" data-test="dialogue-history-search">
    <input type="text" class="dialogue-search-input" placeholder="搜索对话内容…" data-test="dialogue-search-input" />
    <span class="dialogue-search-count hidden" data-test="dialogue-search-count"></span>
  </div>`;

  // Render attitude trends with larger sparkline
  html += `<div class="dialogue-history-attitudes" data-test="dialogue-history-attitudes">`;
  for (const [npcId, data] of Object.entries(attitudeHistory)) {
    const att = data.currentAttitude;
    const attLabel = att >= 30 ? "友善" : att >= 10 ? "中立" : att >= -10 ? "陌生" : att >= -30 ? "冷淡" : "敌意";
    const attCls = att >= 10 ? "att-positive" : att <= -10 ? "att-negative" : "att-neutral";
    const trendIcon = att > 0 ? "↑" : att < 0 ? "↓" : "→";
    const dialogueCount = data.entries.length;
    const sparkline = renderAttitudeSparkline(data.deltas, att, true);
    const positiveCount = data.entries.filter((e) => e.attitudeDelta > 0).length;
    const negativeCount = data.entries.filter((e) => e.attitudeDelta < 0).length;

    html += `<div class="dialogue-history-npc" data-test="dialogue-history-npc-${npcId}" data-npc-id="${escapeAttr(npcId)}">
      <div class="dialogue-history-npc-header">
        <span class="dialogue-history-npc-name">${escapeHtml(data.npcName)}</span>
        <span class="dialogue-history-npc-attitude ${attCls}">${attLabel} (${att >= 0 ? "+" : ""}${att}) ${trendIcon}</span>
      </div>
      <div class="dialogue-history-npc-chart">${sparkline}</div>
      <div class="dialogue-history-npc-stats">
        <span>对话 ${dialogueCount} 次</span>
        <span>好感 ${positiveCount} · 恶感 ${negativeCount}</span>
        <span>最近话题: ${escapeHtml(data.entries[0]?.topic || "无")}</span>
      </div>
    </div>`;
  }
  html += `</div>`;

  // Topic filter
  if (allTopics.length > 1) {
    html += `<div class="dialogue-history-topic-filters" data-test="dialogue-history-topic-filters">
      <span class="dialogue-history-topic-label">话题:</span>
      <button type="button" class="quest-filter-chip active" data-dh-filter-type="topic" data-dh-filter-value="all">全部</button>
      ${allTopics.map((t) => `<button type="button" class="quest-filter-chip" data-dh-filter-type="topic" data-dh-filter-value="${escapeAttr(t)}">${escapeHtml(t)}</button>`).join("")}
    </div>`;
  }

  // --- Phase 34: export + load more ---
  html += `<div class="dialogue-history-actions" data-test="dialogue-history-actions">
    <button type="button" class="dialogue-export-btn" data-test="dialogue-export-btn">导出对话历史</button>
    ${events.length > 20 ? `<span class="dialogue-history-more-count">共 ${events.length} 条，显示最近 20</span>` : ""}
  </div>`;

  // Render dialogue timeline (show up to 20)
  const recentDialogues = events.slice(-20).reverse();
  html += `<div class="dialogue-history-timeline" data-test="dialogue-history-timeline">
    <div class="dialogue-history-timeline-header">
      <h4>对话记录</h4>
      <span class="dialogue-history-timeline-count">${events.length} 条${events.length > 20 ? ` · 最近 20` : ""}</span>
    </div>`;

  for (const ev of recentDialogues) {
    const npcName = ev.target_name || ev.target || "未知";
    const npcId = ev.target || "";
    const topic = ev.topic || "";
    const topicHtml = topic ? `<span class="dialogue-history-topic">${escapeHtml(topic)}</span>` : "";
    const playerLine = ev.player_line ? `<div class="dialogue-history-player">「${escapeHtml(ev.player_line)}」</div>` : "";
    const npcResponse = ev.npc_response ? `<div class="dialogue-history-npc-response">「${escapeHtml(ev.npc_response)}」</div>` : "";
    const attDelta = ev.attitude_delta || 0;
    const attDeltaHtml = attDelta !== 0
      ? `<span class="dialogue-history-attitude-delta ${attDelta > 0 ? "att-positive" : "att-negative"}">${attDelta > 0 ? "+" : ""}${attDelta}</span>`
      : "";
    const turn = ev.turn != null ? `<span class="dialogue-history-turn">#${ev.turn}</span>` : "";

    html += `<div class="dialogue-history-entry" data-test="dialogue-history-entry-${ev.id || ""}" data-npc-id="${escapeAttr(npcId)}" data-topic="${escapeAttr(topic)}" data-searchable="${escapeAttr(((ev.player_line || "") + " " + (ev.npc_response || "")).toLowerCase())}">
      <div class="dialogue-history-entry-header">
        <span class="dialogue-history-npc-label">${escapeHtml(npcName)}</span>
        ${topicHtml}
        ${turn}
        ${attDeltaHtml}
      </div>
      ${playerLine}
      ${npcResponse}
    </div>`;
  }

  html += `</div>`;
  panel.innerHTML = html;

  // Wire up filter interactivity
  const filtersContainer = panel.querySelector(".dialogue-history-filters");
  const topicFiltersContainer = panel.querySelector(".dialogue-history-topic-filters");
  const attitudeSection = panel.querySelector(".dialogue-history-attitudes");
  const timelineList = panel.querySelector(".dialogue-history-timeline");
  const searchInput = panel.querySelector(".dialogue-search-input");
  const searchCount = panel.querySelector(".dialogue-search-count");
  const exportBtn = panel.querySelector(".dialogue-export-btn");

  function applyDialogueFilters() {
    // Determine active NPC filter
    const activeNpcChips = filtersContainer.querySelectorAll("[data-dh-filter-type='npc'].active");
    const activeNpcs = new Set([...activeNpcChips].map((c) => c.dataset.dhFilterValue));
    const showAllNpcs = activeNpcs.has("all");

    // Determine active topic filter
    let activeTopics = null;
    if (topicFiltersContainer) {
      const activeTopicChips = topicFiltersContainer.querySelectorAll("[data-dh-filter-type='topic'].active");
      const topicVals = [...activeTopicChips].map((c) => c.dataset.dhFilterValue);
      if (!topicVals.includes("all")) activeTopics = new Set(topicVals);
    }

    // Determine search text
    const searchTerm = (searchInput?.value || "").trim().toLowerCase();

    // Filter attitude cards
    if (attitudeSection) {
      attitudeSection.querySelectorAll(".dialogue-history-npc").forEach((card) => {
        const cardNpc = card.dataset.npcId;
        card.style.display = (showAllNpcs || activeNpcs.has(cardNpc)) ? "" : "none";
      });
    }

    // Filter timeline entries
    let visibleCount = 0;
    if (timelineList) {
      timelineList.querySelectorAll(".dialogue-history-entry").forEach((entry) => {
        const entryNpc = entry.dataset.npcId;
        const entryTopic = entry.dataset.topic;
        const searchable = entry.dataset.searchable || "";
        const npcMatch = showAllNpcs || activeNpcs.has(entryNpc);
        const topicMatch = !activeTopics || activeTopics.has(entryTopic);
        const searchMatch = !searchTerm || searchable.includes(searchTerm);
        const visible = npcMatch && topicMatch && searchMatch;
        entry.style.display = visible ? "" : "none";
        if (visible) visibleCount++;
      });
    }

    // Update search count
    if (searchCount) {
      if (searchTerm) {
        const totalCount = timelineList?.querySelectorAll(".dialogue-history-entry").length || 0;
        searchCount.textContent = `${visibleCount}/${totalCount} 条`;
        searchCount.classList.remove("hidden");
      } else {
        searchCount.classList.add("hidden");
      }
    }
  }

  function setupChipGroup(container, filterType) {
    if (!container) return;
    container.addEventListener("click", (e) => {
      const chip = e.target.closest(".quest-filter-chip");
      if (!chip) return;
      const value = chip.dataset.dhFilterValue;

      if (value === "all") {
        container.querySelectorAll(`[data-dh-filter-type='${filterType}']`).forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
      } else {
        const allChip = container.querySelector(`[data-dh-filter-value="all"]`);
        if (allChip) allChip.classList.remove("active");
        chip.classList.toggle("active");
        const anyActive = container.querySelector(`[data-dh-filter-type='${filterType}'].active`);
        if (!anyActive && allChip) allChip.classList.add("active");
      }
      applyDialogueFilters();
    });
  }

  setupChipGroup(filtersContainer, "npc");
  setupChipGroup(topicFiltersContainer, "topic");

  // Wire up search
  if (searchInput) {
    searchInput.addEventListener("input", applyDialogueFilters);
  }

  // Wire up export
  if (exportBtn) {
    exportBtn.addEventListener("click", () => {
      const lines = [];
      lines.push("人生纪实 · 对话历史导出");
      lines.push("=".repeat(40));
      lines.push(`导出时间: ${new Date().toLocaleString("zh-CN")}`);
      lines.push(`对话总数: ${totalDialogues}, NPC 数: ${npcCount}`);
      lines.push("");
      for (const ev of events) {
        const npcName = ev.target_name || ev.target || "未知";
        const topic = ev.topic || "";
        const turn = ev.turn != null ? `#${ev.turn}` : "";
        const attDelta = ev.attitude_delta || 0;
        const deltaStr = attDelta !== 0 ? ` [态度${attDelta > 0 ? "+" : ""}${attDelta}]` : "";
        lines.push(`[${turn}] ${npcName}${topic ? " · " + topic : ""}${deltaStr}`);
        if (ev.player_line) lines.push(`  玩家: ${ev.player_line}`);
        if (ev.npc_response) lines.push(`  ${npcName}: ${ev.npc_response}`);
        lines.push("");
      }
      const text = lines.join("\n");
      const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `dialogue-history-${Date.now()}.txt`;
      a.click();
      URL.revokeObjectURL(url);
    });
  }
}

// ===================================================================
// Story / clues / pressure panels (Phase 6)
// ===================================================================
function renderStoryPanel(state) {
  const flags = state.flags || {};
  const seeds = flags.story_seeds;
  if (!seeds) {
    $("#story-panel").innerHTML = "<em>暂无</em>";
    return;
  }
  const progress = flags.story_progress || {};
  const clueCount = Object.values(progress).reduce(
    (sum, tdata) => sum + ((tdata.clues || []).length), 0);
  const allThreads = [];
  if (seeds.main_thread) {
    allThreads.push({
      id: "main_thread",
      title: seeds.main_thread.title || "主线",
      kind: "主线",
    });
  }
  (seeds.side_threads || []).forEach((st) => allThreads.push({
    id: st.id,
    title: st.title || st.id,
    kind: "支线",
  }));
  const knownThreadIds = new Set(allThreads.map((thread) => thread.id));
  Object.keys(progress).forEach((threadId) => {
    if (!knownThreadIds.has(threadId)) {
      allThreads.push({ id: threadId, title: threadId, kind: "线索" });
    }
  });
  const threadStats = allThreads.map((thread) => ({
    ...thread,
    clueCount: ((progress[thread.id] || {}).clues || []).length,
  }));
  const activeThreads = threadStats.filter((thread) => thread.clueCount > 0).length;
  const topThreads = threadStats
    .filter((thread) => thread.clueCount > 0)
    .sort((a, b) => b.clueCount - a.clueCount || (a.id === "main_thread" ? -1 : 1))
    .slice(0, isCompactDensity() ? 2 : 4);
  let html = `<div class="story-progress-overview" data-test="story-progress-overview">
    <div><span>线索总数</span><strong>${clueCount}</strong></div>
    <div><span>活跃线程</span><strong>${activeThreads}/${threadStats.length}</strong></div>
    <div><span>未触发</span><strong>${Math.max(threadStats.length - activeThreads, 0)}</strong></div>
  </div>`;
  if (topThreads.length) {
    html += `<div class="story-thread-progress-list" data-test="story-thread-progress-list">${topThreads.map((thread) =>
      `<div class="story-thread-progress" data-test="story-thread-progress-${escapeAttr(thread.id)}">
        <span>${escapeHtml(thread.kind)} · ${escapeHtml(thread.title)}</span><strong>${thread.clueCount}条</strong>
      </div>`
    ).join("")}</div>`;
  }
  if (seeds.main_thread) {
    const mt = seeds.main_thread;
    html += `<div class="story-thread">
      <div class="thread-title">${escapeHtml(mt.title || "")}</div>
      <div class="thread-hook">${escapeHtml(mt.premise || "")}</div>
      <div class="thread-hook">当前线索: ${clueCount} 条</div>
    </div>`;
  }
  const sideThreads = isCompactDensity()
    ? (seeds.side_threads || []).slice(0, 3)
    : (seeds.side_threads || []);
  if (sideThreads.length) {
    html += sideThreads.map((st) =>
      `<div class="side-thread">
        <div class="thread-title">${escapeHtml(st.title || "")}</div>
      </div>`
    ).join("");
    if (isCompactDensity() && (seeds.side_threads || []).length > sideThreads.length) {
      html += `<div class="compact-more">另有 ${(seeds.side_threads || []).length - sideThreads.length} 条支线，切换详细查看</div>`;
    }
  }
  $("#story-panel").innerHTML = html || "<em>暂无</em>";
}

function renderCluesPanel(state) {
  const flags = state.flags || {};
  const progress = flags.story_progress;
  if (!progress || Object.keys(progress).length === 0) {
    $("#clues-panel").innerHTML = renderEmptyGuide("🔍", "暂无线索", [
      { label: "与 NPC 交谈", hint: "打听消息收集情报" },
      { label: "仔细观察环境", hint: "发现隐藏细节" },
      { label: "探索不同地点", hint: "扩大搜索范围" },
    ]);
    return;
  }
  const seeds = flags.story_seeds || {};
  const sideById = {};
  (seeds.side_threads || []).forEach((st) => { sideById[st.id] = st; });
  const threadNames = { main_thread: seeds.main_thread?.title || "主线" };
  Object.entries(sideById).forEach(([id, st]) => { threadNames[id] = st.title || id; });

  const entries = Object.entries(progress)
    .map(([tid, tdata]) => ({
      tid,
      clues: attachClueEvents(tid, tdata.clues || [], state.events || []).slice().reverse(),
      tname: threadNames[tid] || tid,
    }))
    .sort((a, b) => {
      if (a.tid === "main_thread") return -1;
      if (b.tid === "main_thread") return 1;
      return b.clues.length - a.clues.length || a.tname.localeCompare(b.tname, "zh-Hans-CN");
    });

  const totalClues = entries.reduce((sum, entry) => sum + entry.clues.length, 0);
  let html = `<div class="clue-summary" data-test="clue-summary">共 ${totalClues} 条线索 · ${entries.length} 个线程</div>`;
  if (totalClues > 0) {
    const chronologicalEntries = Object.entries(progress)
      .map(([tid, tdata]) => ({
        tid,
        clues: tdata.clues || [],
        tname: threadNames[tid] || tid,
      }))
      .filter((entry) => entry.clues.length > 0);
    const latestEntry = chronologicalEntries[chronologicalEntries.length - 1];
    const latestClue = latestEntry?.clues[latestEntry.clues.length - 1];
    const activeEntry = entries
      .filter((entry) => entry.clues.length > 0)
      .sort((a, b) => b.clues.length - a.clues.length || (a.tid === "main_thread" ? -1 : 1))[0];
    html += `<div class="clue-insight-summary" data-test="clue-insight-summary">
      <div><span>最新线索</span>${escapeHtml(latestClue?.clue || "暂无")}</div>
      <div><span>活跃线程</span>${escapeHtml(activeEntry ? `${activeEntry.tname} · ${activeEntry.clues.length}条` : "暂无")}</div>
    </div>`;
  }
  for (const entry of entries) {
    const clues = entry.clues;
    html += `<div class="thread-group-title ${entry.tid === 'main_thread' ? 'main-thread' : ''}">
      <span>${escapeHtml(entry.tname)}</span><span>${clues.length}条</span>
    </div>`;
    if (clues.length === 0) {
      html += "<em>暂无线索</em>";
    } else {
      html += clues.map((c, idx) => {
        let meta = "";
        if (c.source_entity) meta += `<span>来源: ${escapeHtml(c.source_entity)}</span>`;
        if (c.location_id) meta += `<span>地点: ${escapeHtml(c.location_id)}</span>`;
        if (c.evidence_item) meta += `<span>证物: ${escapeHtml(c.evidence_item)}</span>`;
        const eventLink = c.event_id
          ? `<button type="button" class="clue-event-link" data-test="clue-event-${escapeAttr(c.event_id)}" onclick="focusTimelineEvent('${escapeAttr(c.event_id)}')">查看事件</button>`
          : "";
        return `<div class="clue-card ${idx === 0 ? 'latest' : ''}">
          <div class="clue-text">${idx === 0 ? '<span class="clue-latest">新近</span>' : ''}${escapeHtml(c.clue || "")}</div>
          ${meta || eventLink ? `<div class="clue-meta">${meta}${eventLink}</div>` : ""}
        </div>`;
      }).join("");
    }
  }
  $("#clues-panel").innerHTML = html;
}

function attachClueEvents(threadId, clues, events) {
  return clues.map((clue) => {
    const matched = (events || []).find((ev) =>
      ev.type === "record_clue" &&
      ev.thread_id === threadId &&
      ev.clue === clue.clue
    );
    return matched ? { ...clue, event_id: matched.id } : clue;
  });
}

const QUEST_REGION_NAMES = {
  yangzhou: "扬州", guazhou: "瓜洲", nanjing: "南京",
  suzhou: "苏州", hangzhou: "杭州", huaian: "淮安", xuzhou: "徐州",
};
const QUEST_REGION_CHAIN = ["yangzhou", "guazhou", "nanjing", "suzhou", "hangzhou", "huaian", "xuzhou"];

function renderQuestLogPanel(state) {
  const flags = state.flags || {};
  const questLog = flags.quest_log;
  if (!questLog || !questLog.entries || questLog.entries.length === 0) {
    $("#quest-panel").innerHTML = renderEmptyGuide("📋", "暂无调查记录", [
      { label: "探索各地", hint: "发现调查线索" },
      { label: "与 NPC 交谈", hint: "了解各地情况" },
      { label: "推进主线", hint: "解锁调查里程碑" },
    ]);
    return;
  }
  const entries = questLog.entries || [];
  const active = entries.filter((e) => e.status === "active");
  const completed = entries.filter((e) => e.status === "completed");
  const locked = entries.filter((e) => e.status === "locked");
  const regionSet = new Set(entries.map((e) => e.region).filter(Boolean));
  const regions = [...regionSet];

  // Overview bar
  let html = `<div class="quest-overview" data-test="quest-overview">
    <div><span>进行中</span><strong>${active.length}</strong></div>
    <div><span>已完成</span><strong>${completed.length}</strong></div>
    <div><span>未解锁</span><strong>${locked.length}</strong></div>
    <div><span>地区</span><strong>${regions.length}</strong></div>
  </div>`;

  // Cross-region investigation flow map with clue counts
  const activeRegions = new Set(entries.filter((e) => e.status === "active").map((e) => e.region));
  const completedRegions = new Set(entries.filter((e) => e.status === "completed").map((e) => e.region));
  const hasAnyRegion = QUEST_REGION_CHAIN.some((r) => activeRegions.has(r) || completedRegions.has(r));
  if (hasAnyRegion) {
    // Get clue counts per region from story progress
    const storyProgress = flags.story_progress || {};
    const storyThreads = flags.story_threads || {};
    const clueCountsByRegion = {};
    for (const [threadId, prog] of Object.entries(storyProgress)) {
      const thread = storyThreads[threadId] || {};
      const threadRegion = thread.region || "yangzhou";
      const clueCount = ((prog || {}).clues || []).length;
      clueCountsByRegion[threadRegion] = (clueCountsByRegion[threadRegion] || 0) + clueCount;
    }

    const nodes = QUEST_REGION_CHAIN.map((r) => {
      const rEntries = entries.filter((e) => e.region === r);
      const rCompleted = rEntries.filter((e) => e.status === "completed").length;
      const rTotal = rEntries.length;
      const clueCount = clueCountsByRegion[r] || 0;
      let cls = "locked";
      if (activeRegions.has(r)) cls = "active";
      else if (rCompleted === rTotal && rTotal > 0) cls = "completed";
      const label = QUEST_REGION_NAMES[r] || r;
      return `<div class="quest-flow-node ${cls}" data-test="quest-flow-${r}" data-region="${escapeAttr(r)}">
        <span class="quest-flow-dot"></span>
        <span class="quest-flow-label">${escapeHtml(label)}</span>
        <div class="quest-flow-stats">
          ${rTotal > 0 ? `<span class="quest-flow-count">${rCompleted}/${rTotal}</span>` : ""}
          ${clueCount > 0 ? `<span class="quest-flow-clues" title="线索数">${clueCount} 线索</span>` : ""}
        </div>
      </div>`;
    });
    const connectors = QUEST_REGION_CHAIN.slice(0, -1).map((r, i) => {
      const next = QUEST_REGION_CHAIN[i + 1];
      const bothDone = completedRegions.has(r) && completedRegions.has(next);
      const eitherActive = activeRegions.has(r) || activeRegions.has(next);
      const cls = bothDone ? "done" : eitherActive ? "active" : "";
      return `<span class="quest-flow-connector ${cls}"></span>`;
    });
    let flowHtml = "";
    for (let i = 0; i < nodes.length; i++) {
      flowHtml += nodes[i];
      if (i < connectors.length) flowHtml += connectors[i];
    }
    html += `<div class="quest-flow" data-test="quest-flow">${flowHtml}</div>`;

    // Region detail expandable area
    html += `<div class="quest-flow-detail" data-test="quest-flow-detail" style="display:none"></div>`;
  }

  // Region progress summary
  if (regions.length > 0) {
    const regionStats = regions.map((r) => {
      const rEntries = entries.filter((e) => e.region === r);
      const rActive = rEntries.filter((e) => e.status === "active").length;
      const rCompleted = rEntries.filter((e) => e.status === "completed").length;
      const rTotal = rEntries.length;
      const pct = rTotal > 0 ? Math.round((rCompleted / rTotal) * 100) : 0;
      const label = QUEST_REGION_NAMES[r] || r;
      return { region: r, label, active: rActive, completed: rCompleted, total: rTotal, pct };
    }).sort((a, b) => b.pct - a.pct || b.total - a.total);

    html += `<div class="quest-regions" data-test="quest-regions">${regionStats.map((rs) =>
      `<div class="quest-region" data-test="quest-region-${escapeAttr(rs.region)}">
        <div class="quest-region-header">
          <span class="quest-region-name">${escapeHtml(rs.label)}</span>
          <span class="quest-region-progress">${rs.completed}/${rs.total}</span>
        </div>
        <div class="quest-region-bar"><span style="width:${rs.pct}%"></span></div>
      </div>`
    ).join("")}</div>`;
  }

  // Entry list (active first, then completed, then locked)
  const sortedEntries = [
    ...active.map((e) => ({ ...e, _order: 0 })),
    ...completed.map((e) => ({ ...e, _order: 1 })),
    ...locked.map((e) => ({ ...e, _order: 2 })),
  ];
  const visibleEntries = isCompactDensity() ? sortedEntries.slice(0, 5) : sortedEntries;
  if (visibleEntries.length > 0) {
    html += `<div class="quest-entries" data-test="quest-entries">${visibleEntries.map((entry) => {
      const statusLabel = entry.status === "active" ? "进行中" : entry.status === "completed" ? "已完成" : "未解锁";
      const statusCls = entry.status === "active" ? "active" : entry.status === "completed" ? "completed" : "locked";
      const regionLabel = entry.region ? (QUEST_REGION_NAMES[entry.region] || entry.region) : "";
      return `<div class="quest-entry ${statusCls}" data-test="quest-entry-${escapeAttr(entry.id)}">
        <div class="quest-entry-header">
          <span class="quest-entry-status ${statusCls}">${statusLabel}</span>
          ${regionLabel ? `<span class="quest-entry-region">${escapeHtml(regionLabel)}</span>` : ""}
        </div>
        <div class="quest-entry-title">${escapeHtml(entry.title)}</div>
        ${entry.description ? `<div class="quest-entry-desc">${escapeHtml(entry.description)}</div>` : ""}
      </div>`;
    }).join("")}</div>`;
    if (isCompactDensity() && sortedEntries.length > visibleEntries.length) {
      html += `<div class="compact-more">另有 ${sortedEntries.length - visibleEntries.length} 条记录，切换详细查看</div>`;
    }
  }

  // Quest event timeline with filters
  const questEvents = (state.events || []).filter((ev) => ev.type === "quest_log");
  if (questEvents.length > 0) {
    const timelineEvents = isCompactDensity() ? questEvents.slice(-5) : questEvents.slice(-10);

    // Collect unique regions and statuses for filter chips
    const tlRegions = [...new Set(questEvents.map((ev) => ev.region).filter(Boolean))];
    const tlStatuses = [...new Set(questEvents.map((ev) => ev.status).filter(Boolean))];
    const statusLabels = { active: "进行中", completed: "已完成", locked: "未解锁" };
    const statusIcons = { completed: "✓", active: "◉", locked: "○" };

    // Summary stats
    const totalQuestEvents = questEvents.length;
    const recentRegion = questEvents[questEvents.length - 1]?.region;
    const recentRegionLabel = recentRegion ? (QUEST_REGION_NAMES[recentRegion] || recentRegion) : "";

    html += `<div class="quest-timeline" data-test="quest-timeline">
      <div class="quest-timeline-header">
        <div class="quest-timeline-title">调查时间线</div>
        <div class="quest-timeline-summary">${totalQuestEvents} 条记录${recentRegionLabel ? ` · 最近: ${escapeHtml(recentRegionLabel)}` : ""}</div>
      </div>
      <div class="quest-timeline-filters" data-test="quest-timeline-filters">
        <button type="button" class="quest-filter-chip active" data-filter-type="region" data-filter-value="all">全部</button>
        ${tlRegions.map((r) => `<button type="button" class="quest-filter-chip" data-filter-type="region" data-filter-value="${escapeAttr(r)}">${escapeHtml(QUEST_REGION_NAMES[r] || r)}</button>`).join("")}
        ${tlStatuses.length > 1 ? tlStatuses.map((s) => `<button type="button" class="quest-filter-chip" data-filter-type="status" data-filter-value="${escapeAttr(s)}">${statusLabels[s] || s}</button>`).join("") : ""}
      </div>
      <div class="quest-timeline-list" data-test="quest-timeline-list">
        ${timelineEvents.map((ev) => {
          const regionLabel = ev.region ? (QUEST_REGION_NAMES[ev.region] || ev.region) : "";
          const statusIcon = statusIcons[ev.status] || "○";
          const statusCls = ev.status || "locked";
          const timestamp = ev.timestamp ? ` · ${formatTimestamp(ev.timestamp)}` : "";
          return `<div class="quest-timeline-item ${statusCls}" data-region="${escapeAttr(ev.region || "")}" data-status="${escapeAttr(ev.status || "")}">
            <span class="quest-timeline-icon">${statusIcon}</span>
            <span class="quest-timeline-text">${escapeHtml(ev.summary || ev.entry_id || "")}</span>
            <div class="quest-timeline-meta">
              ${regionLabel ? `<span class="quest-timeline-region">${escapeHtml(regionLabel)}</span>` : ""}
              ${timestamp ? `<span class="quest-timeline-time">${timestamp}</span>` : ""}
            </div>
          </div>`;
        }).join("")}
      </div>
    </div>`;
  }

  $("#quest-panel").innerHTML = html;

  // Quest timeline filter interactivity
  const filtersContainer = $("#quest-panel")?.querySelector(".quest-timeline-filters");
  const timelineList = $("#quest-panel")?.querySelector(".quest-timeline-list");
  if (filtersContainer && timelineList) {
    filtersContainer.addEventListener("click", (e) => {
      const chip = e.target.closest(".quest-filter-chip");
      if (!chip) return;
      const filterType = chip.dataset.filterType;
      const filterValue = chip.dataset.filterValue;

      // Toggle active state
      if (filterType === "region" && filterValue === "all") {
        filtersContainer.querySelectorAll("[data-filter-type='region']").forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
      } else {
        const allChip = filtersContainer.querySelector('[data-filter-value="all"]');
        if (allChip) allChip.classList.remove("active");
        chip.classList.toggle("active");
        // If no chip is active, activate "all"
        const anyActive = filtersContainer.querySelector(".quest-filter-chip.active");
        if (!anyActive && allChip) allChip.classList.add("active");
      }

      // Determine active filters
      const activeRegions = new Set();
      const activeStatuses = new Set();
      filtersContainer.querySelectorAll(".quest-filter-chip.active").forEach((c) => {
        if (c.dataset.filterType === "region") activeRegions.add(c.dataset.filterValue);
        if (c.dataset.filterType === "status") activeStatuses.add(c.dataset.filterValue);
      });
      const showAll = activeRegions.has("all");

      // Filter timeline items
      timelineList.querySelectorAll(".quest-timeline-item").forEach((item) => {
        const itemRegion = item.dataset.region;
        const itemStatus = item.dataset.status;
        const regionMatch = showAll || activeRegions.has(itemRegion);
        const statusMatch = activeStatuses.size === 0 || activeStatuses.has(itemStatus);
        item.style.display = regionMatch && statusMatch ? "" : "none";
      });
    });
  }

  // Quest flow node click to expand region details
  const flowContainer = $("#quest-panel")?.querySelector(".quest-flow");
  const detailContainer = $("#quest-panel")?.querySelector(".quest-flow-detail");
  if (flowContainer && detailContainer) {
    flowContainer.addEventListener("click", (e) => {
      const node = e.target.closest(".quest-flow-node");
      if (!node) return;
      const region = node.dataset.region;
      if (!region) return;

      // Toggle active state
      const wasActive = node.classList.contains("selected");
      flowContainer.querySelectorAll(".quest-flow-node").forEach((n) => n.classList.remove("selected"));
      if (!wasActive) {
        node.classList.add("selected");
        // Show detail for this region
        const regionEntries = entries.filter((entry) => entry.region === region);
        const regionLabel = QUEST_REGION_NAMES[region] || region;
        if (regionEntries.length > 0) {
          detailContainer.style.display = "block";
          detailContainer.innerHTML = `<div class="quest-flow-detail-header">
            <span class="quest-flow-detail-title">${escapeHtml(regionLabel)} 调查详情</span>
            <button type="button" class="quest-flow-detail-close" data-test="quest-flow-detail-close">×</button>
          </div>
          <div class="quest-flow-detail-entries">
            ${regionEntries.map((entry) => {
              const statusLabel = entry.status === "active" ? "◉" : entry.status === "completed" ? "✓" : "○";
              const statusCls = entry.status || "locked";
              return `<div class="quest-flow-detail-entry ${statusCls}">
                <span class="quest-flow-detail-icon">${statusLabel}</span>
                <div class="quest-flow-detail-content">
                  <div class="quest-flow-detail-entry-title">${escapeHtml(entry.title || entry.id)}</div>
                  ${entry.description ? `<div class="quest-flow-detail-entry-desc">${escapeHtml(entry.description)}</div>` : ""}
                </div>
              </div>`;
            }).join("")}
          </div>`;
        } else {
          detailContainer.style.display = "none";
        }
      } else {
        detailContainer.style.display = "none";
      }
    });

    detailContainer.addEventListener("click", (e) => {
      if (e.target.closest(".quest-flow-detail-close")) {
        detailContainer.style.display = "none";
        flowContainer.querySelectorAll(".quest-flow-node").forEach((n) => n.classList.remove("selected"));
      }
    });
  }
}

function renderPressurePanel(state) {
  const flags = state.flags || {};
  const clocks = flags.pressure_clocks;
  if (!clocks || Object.keys(clocks).length === 0) {
    $("#pressure-panel").innerHTML = renderEmptyGuide("⏱", "暂无压力", [
      { label: "推进剧情", hint: "触发新的压力事件" },
      { label: "与 NPC 互动", hint: "了解当前局势" },
    ]);
    return;
  }
  let html = "";
  for (const [cid, cdata] of Object.entries(clocks)) {
    const value = cdata.value || 0;
    const dangerAt = cdata.danger_at || 1;
    const pct = Math.min(100, Math.max(0, (value / Math.max(dangerAt, 1)) * 100));
    let cls = "safe";
    if (pct >= 80) cls = "danger";
    else if (pct >= 50) cls = "warn";
    const history = cdata.history || [];
    const trend = renderPressureTrend(history);
    const sparkline = renderPressureSparkline(history, cls);
    const action = pressureClockAction(cid, value, dangerAt);
    html += `<div class="pressure-clock ${cls}" data-test="pressure-clock-${escapeAttr(cid)}">
      <div class="clock-label">${escapeHtml(cid)}</div>
      <div class="pressure-bar"><span class="fill ${cls}" style="width:${pct}%"></span></div>
      <div class="clock-value">${value} / 危险线 ${dangerAt} ${trend} ${sparkline}</div>
      ${action ? `<button type="button" class="pressure-action" data-test="pressure-action-${escapeAttr(cid)}" data-action="${escapeAttr(action)}">应对行动</button>` : ""}
    </div>`;
  }
  $("#pressure-panel").innerHTML = html;
  $("#pressure-panel").querySelectorAll(".pressure-action").forEach((btn) => {
    btn.addEventListener("click", () => handleTurn(btn.dataset.action));
  });
}

function pressureClockAction(clockId, value, dangerAt) {
  const ratio = value / Math.max(dangerAt || 1, 1);
  if (ratio < 0.5) return null;
  const urgency = ratio >= 0.8 ? "当务之急" : "需要尽快处理";
  return `${urgency}：我先应对${clockId}，梳理相关线索，安抚关键人物，避免局势继续恶化。`;
}

function renderPressureTrend(history) {
  if (history.length < 2) return "";
  const prev = history[history.length - 2];
  const curr = history[history.length - 1];
  if (curr > prev) return '<span class="trend-up" title="上升">↑</span>';
  if (curr < prev) return '<span class="trend-down" title="下降">↓</span>';
  return '<span class="trend-stable" title="持平">→</span>';
}

function renderPressureSparkline(history, cls) {
  if (history.length < 2) return "";
  const w = 40, h = 14;
  const max = Math.max(...history, 1);
  const step = w / Math.max(history.length - 1, 1);
  const pts = history.map((v, i) => `${(i * step).toFixed(1)},${(h - (v / max) * h).toFixed(1)}`).join(" ");
  const color = cls === "danger" ? "#e85d4a" : cls === "warn" ? "#d4a84a" : "#8aad4a";
  return `<svg class="pressure-sparkline" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><polyline points="${pts}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
}

function renderEndingPanel(state) {
  const flags = state.flags || {};
  const progress = flags.ending_progress || { endings: [] };
  const endings = progress.endings || [];
  const seeds = flags.ending_seeds || [];
  const stepsData = flags.ending_steps || {};
  if (endings.length === 0 && seeds.length === 0) {
    $("#ending-panel").innerHTML = renderEmptyGuide("🎯", "结局未解锁", [
      { label: "推进主线剧情", hint: "解锁结局方向" },
      { label: "收集更多线索", hint: "揭示故事全貌" },
      { label: "完成支线任务", hint: "影响最终结局" },
    ]);
    return;
  }
  // Build seed cards with progress
  const seedCards = seeds.map((s) => {
    const steps = stepsData[s.id] || [];
    const completedCount = steps.filter((st) => st.completed).length;
    const totalCount = steps.length;
    const progressHtml = totalCount > 0
      ? `<div class="ending-progress" data-test="ending-progress-${s.id}">
          <div class="ending-progress-bar"><div class="ending-progress-fill" style="width:${(completedCount / totalCount * 100).toFixed(0)}%"></div></div>
          <div class="ending-progress-text">${completedCount}/${totalCount} 步骤</div>
          ${steps.map((st) => `<div class="ending-step ${st.completed ? 'completed' : ''}" data-test="ending-step-${s.id}-${st.id}">${st.completed ? '✓' : '○'} ${escapeHtml(st.label)}</div>`).join("")}
        </div>`
      : '';
    return `<div class="ending-seed" data-test="ending-seed-${s.id}">
      <div class="ending-title">${escapeHtml(s.title || s.id)}</div>
      <div class="ending-hint">${escapeHtml(s.trigger_hint || '')}</div>
      ${progressHtml}
    </div>`;
  }).join("");
  // Build recorded ending cards
  const endingCards = endings.map((e) =>
    `<div class="ending-card ${e.final ? 'final' : ''}" data-test="ending-${e.id}">
      <div class="ending-title">${escapeHtml(e.title || e.id)}${e.final ? ' <span class="ending-final">终局</span>' : ''}</div>
      <div class="ending-summary">${escapeHtml(e.summary || '')}</div>
      ${e.outcome ? `<div class="ending-outcome">${escapeHtml(e.outcome)}</div>` : ''}
    </div>`
  ).join("");
  $("#ending-panel").innerHTML = seedCards + endingCards;
}

// ===================================================================
// Skills panel (Phase 6: 修炼/技能成长)
// ===================================================================
function renderSkillsPanel(state) {
  const player = (state.entities || []).find((e) => e.id === "player");
  if (!player) {
    $("#skills-panel").innerHTML = renderEmptyGuide("📚", "暂无技能", [
      { label: "向 NPC 学习", hint: "请教特定技能" },
      { label: "自主修炼", hint: "通过实践提升" },
    ]);
    return;
  }
  const skills = (player.attributes || {}).skills || {};
  const entries = Object.entries(skills);
  if (entries.length === 0) {
    $("#skills-panel").innerHTML = renderEmptyGuide("📚", "尚未习得技能", [
      { label: "向 NPC 学习", action: "我想向在场的人请教一些技艺。", hint: "拜师学艺" },
      { label: "自主修炼", action: "我想花时间练习一下基本功。", hint: "勤学苦练" },
    ]);
    return;
  }

  // XP needed per level: level*10 + 5 (level 0→1 needs 5, 1→2 needs 15, etc.)
  const xpForLevel = (lvl) => lvl * 10 + 5;

  $("#skills-panel").innerHTML = entries.map(([id, s]) => {
    const name = escapeHtml(s.name || id);
    const level = s.level ?? 0;
    const xp = s.xp ?? 0;
    const needed = xpForLevel(level);
    const pct = Math.min(100, Math.round((xp / needed) * 100));
    const note = s.note ? `<div class="skill-note">${escapeHtml(s.note)}</div>` : "";
    return `<div class="skill-card" data-test="skill-${id}">
      <div class="skill-header">
        <span class="skill-name">${name}</span>
        <span class="skill-level">Lv.${level}</span>
      </div>
      <div class="skill-xp-bar">
        <div class="skill-xp-fill" style="width:${pct}%"></div>
      </div>
      <div class="skill-meta">经验 ${xp}/${needed}</div>
      ${note}
    </div>`;
  }).join("");
}

// ===================================================================
// Evolutions panel (Phase 10: 世界演化)
// ===================================================================
function renderEvolutionsPanel(state) {
  const panel = $("#evolutions-panel");
  if (!panel) return;
  const registry = ((state.flags || {}).evolution_registry) || [];
  if (registry.length === 0) {
    panel.innerHTML = renderEmptyGuide("🌍", "世界静止中", [
      { label: "推进剧情", hint: "触发世界演化" },
      { label: "与 NPC 互动", hint: "影响周围事物" },
    ]);
    return;
  }

  const entities = state.entities || [];
  const entityMap = {};
  entities.forEach((e) => { entityMap[e.id] = e; });

  const frequencyLabels = {
    every_turn: "每回合",
    every_2_turns: "隔一回合",
    every_5_turns: "低频",
    dormant: "暂停",
  };
  const frequencyOrder = { every_turn: 0, every_2_turns: 1, every_5_turns: 2, dormant: 3 };

  const sorted = [...registry].sort((a, b) =>
    (frequencyOrder[a.frequency] ?? 9) - (frequencyOrder[b.frequency] ?? 9));

  const visible = isCompactDensity() ? sorted.slice(0, 3) : sorted;

  const currentTurn = ((state.flags || {}).turn_index)
    || (state.events || []).length;

  panel.innerHTML = visible.map((entry) => {
    const entity = entityMap[entry.entity_id];
    const name = entity ? entity.name : entry.entity_id;
    const location = entity ? entity.location : "未知";
    const freqLabel = frequencyLabels[entry.frequency] || entry.frequency;
    const isDormant = entry.frequency === "dormant";
    const freqClass = isDormant ? "evo-freq-dormant" : "evo-freq-active";
    const reason = entry.reason ? `<div class="evo-reason">${escapeHtml(entry.reason)}</div>` : "";
    const lastTurn = entry.last_evolved_turn;
    const turnAgo = (lastTurn != null && currentTurn > lastTurn)
      ? currentTurn - lastTurn : null;
    const turnInfo = turnAgo != null
      ? `回合 ${lastTurn} (${turnAgo} 回合前)`
      : (lastTurn != null ? `回合 ${lastTurn}` : "—");
    return `<div class="evo-card" data-test="evolution-${entry.entity_id}">
      <div class="evo-header">
        <span class="evo-name">${escapeHtml(name)}</span>
        <span class="${freqClass}">${freqLabel}</span>
      </div>
      <div class="evo-meta">位置: ${escapeHtml(location || "—")} · 上次演化: ${turnInfo}</div>
      ${reason}
    </div>`;
  }).join("");

  if (isCompactDensity() && sorted.length > visible.length) {
    panel.innerHTML += `<div class="compact-more">另有 ${sorted.length - visible.length} 个演化实体，切换详细查看</div>`;
  }
}

// ===================================================================
// Review / replay panel (Phase 7: 回放/复盘体验增强)
// ===================================================================
function renderReviewPanel(state) {
  const events = state.events || [];
  const flags = state.flags || {};
  const progress = flags.story_progress || {};
  const cluesTotal = Object.values(progress).reduce(
    (sum, t) => sum + ((t.clues || []).length), 0);
  const turnsPlayed = events.length;
  const player = (state.entities || []).find((e) => e.id === "player");
  const npcsMet = new Set((events || [])
    .filter((e) => e.actor && e.actor !== "player")
    .map((e) => e.actor)).size;

  let html = `<div class="review-stats">
    <div class="review-stat"><span class="review-stat-value">${turnsPlayed}</span> 回合</div>
    <div class="review-stat"><span class="review-stat-value">${cluesTotal}</span> 线索</div>
    <div class="review-stat"><span class="review-stat-value">${npcsMet}</span> NPC</div>
  </div>`;
  html += `<button class="review-open-btn" data-test="open-review">查看完整回顾</button>`;
  html += `<button class="review-open-btn replay-open-btn" data-test="open-replay">回放播放器</button>`;
  $("#review-panel").innerHTML = html;
}

function buildReviewText(turns) {
  if (!turns || !turns.length) return "暂无游戏记录";
  const lines = ["人生纪实 · 明朝篇 · 故事回顾", ""];
  turns.forEach((t) => {
    const turnNum = t.turn !== undefined ? `回合 ${t.turn}` : "回合";
    lines.push(`## ${turnNum}`);
    lines.push(`你：${t.player_input || ""}`);
    lines.push(`GM：${t.narration || ""}`);
    lines.push("");
  });
  return lines.join("\n").trimEnd() + "\n";
}

function renderReviewSummary(turns) {
  const total = turns.length;
  const playerWords = turns.reduce((sum, t) => sum + String(t.player_input || "").length, 0);
  const gmWords = turns.reduce((sum, t) => sum + String(t.narration || "").length, 0);
  const latest = turns[turns.length - 1] || {};
  const latestTurn = latest.turn !== undefined ? `回合 ${latest.turn}` : "最近回合";
  const latestInput = String(latest.player_input || "").trim();
  const latestText = latestInput.length > 18 ? `${latestInput.slice(0, 18)}…` : (latestInput || "暂无输入");
  return `<div class="review-summary" data-test="review-summary">
    <div><span>${total}</span>总回合</div>
    <div><span>${playerWords}</span>玩家字数</div>
    <div><span>${gmWords}</span>GM字数</div>
    <div><span>${escapeHtml(latestTurn)}</span>${escapeHtml(latestText)}</div>
  </div>`;
}

function renderReviewHighlights(turns) {
  const highlights = turns.slice(-3).reverse();
  if (!highlights.length) return "";
  return `<div class="review-highlights" data-test="review-highlights">
    <div class="review-highlights-title">重点摘录</div>
    ${highlights.map((t) => {
      const turnNum = t.turn !== undefined ? `回合 ${t.turn}` : "最近回合";
      const action = compactReviewText(t.player_input || "暂无输入", 22);
      const result = compactReviewText(t.narration || "暂无叙述", 34);
      return `<div class="review-highlight-card" data-test="review-highlight-${t.turn || 0}">
        <span>${escapeHtml(turnNum)}</span>
        <strong>${escapeHtml(action)}</strong>
        <em>${escapeHtml(result)}</em>
      </div>`;
    }).join("")}
  </div>`;
}

function compactReviewText(text, maxLen) {
  const s = String(text || "").replace(/\s+/g, " ").trim();
  return s.length > maxLen ? `${s.slice(0, maxLen)}…` : s;
}

function renderReviewDetail(turns, total, has_more) {
  if (!turns || !turns.length) return "<em>暂无游戏记录</em>";
  const text = buildReviewText(turns);
  const summary = renderReviewSummary(turns);
  const highlights = renderReviewHighlights(turns);
  const loadedCount = turns.length;
  const totalDisplay = total !== undefined ? total : loadedCount;
  const loadMoreBtn = has_more ? `<div class="review-load-more" data-test="review-load-more">
    <button type="button" data-test="review-load-more-btn">加载更早回合 (已加载 ${loadedCount}/${totalDisplay})</button>
  </div>` : (totalDisplay > loadedCount ? `<div class="review-load-info">已加载全部 ${totalDisplay} 个回合</div>` : '');
  const actions = `<div class="review-actions">
    <button type="button" data-test="review-jump-latest">跳到最新</button>
    <button data-test="copy-review" data-review-text="${escapeAttr(text)}">复制文本</button>
    <button data-test="download-review" data-review-text="${escapeAttr(text)}">下载文本</button>
  </div>`;
  const typeFilters = renderReviewTypeFilters(turns);
  const filter = `<div class="review-filter">
    <input type="search" data-test="review-filter-input" placeholder="筛选回合内容" aria-label="筛选复盘回合" />
    <div class="review-filter-count" data-test="review-filter-count">共 ${turns.length} 个回合</div>
    <div class="review-match-controls hidden" data-review-match-controls data-test="review-match-controls">
      <button type="button" data-review-match-nav="prev" data-test="review-match-prev">上一个</button>
      <span data-review-match-index data-test="review-match-index">0 / 0</span>
      <button type="button" data-review-match-nav="next" data-test="review-match-next">下一个</button>
    </div>
  </div>`;
  // Show turns chronologically (oldest first)
  return `${summary}${highlights}${actions}${typeFilters}${filter}<div class="review-timeline">${turns.map((t) => {
    const turnNum = t.turn !== undefined ? `回合 ${t.turn}` : "";
    const playerBubble = escapeHtml(t.player_input || "");
    const narration = escapeHtml(t.narration || "");
    const searchable = `${turnNum} ${t.player_input || ""} ${t.narration || ""}`;
    const reviewType = detectReviewTurnType(t);
    return `<div class="review-chapter" data-test="review-turn-${t.turn || 0}" data-review-chapter data-review-type="${reviewType}" data-review-search="${escapeAttr(searchable.toLowerCase())}">
      <div class="review-turn-label">${turnNum}<span class="review-type-badge type-${reviewType}" data-test="review-type-${t.turn || 0}">${EVENT_TYPE_LABELS[reviewType]}</span></div>
      <div class="review-bubble review-player">${playerBubble}</div>
      <div class="review-bubble review-gm">${narration}</div>
    </div>`;
  }).join("")}</div>${loadMoreBtn}<div class="review-filter-empty hidden" data-test="review-filter-empty">无匹配回合 <button type="button" data-test="review-filter-clear">清空筛选</button></div>`;
}

function bindReviewEvents(body) {
  const filterInput = body.querySelector('[data-test="review-filter-input"]');
  if (filterInput) filterInput.addEventListener("input", () => applyReviewFilter(body));
  body.querySelectorAll("[data-review-type-filter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      body.querySelectorAll("[data-review-type-filter]").forEach((el) => el.classList.remove("active"));
      btn.classList.add("active");
      applyReviewFilter(body);
    });
  });
  const loadMoreBtn = body.querySelector('[data-test="review-load-more-btn"]');
  if (loadMoreBtn) {
    loadMoreBtn.addEventListener("click", async () => {
      const timeline = body.querySelector(".review-timeline");
      const existingChapters = timeline ? timeline.querySelectorAll("[data-review-chapter]").length : 0;
      loadMoreBtn.textContent = "加载中...";
      loadMoreBtn.disabled = true;
      try {
        const data = await api(`/api/audit?limit=50&offset=${existingChapters}`);
        if (data.turns && data.turns.length) {
          const tempDiv = document.createElement("div");
          tempDiv.innerHTML = data.turns.map((t) => {
            const turnNum = t.turn !== undefined ? `回合 ${t.turn}` : "";
            const playerBubble = escapeHtml(t.player_input || "");
            const narration = escapeHtml(t.narration || "");
            const searchable = `${turnNum} ${t.player_input || ""} ${t.narration || ""}`;
            const reviewType = detectReviewTurnType(t);
            return `<div class="review-chapter" data-test="review-turn-${t.turn || 0}" data-review-chapter data-review-type="${reviewType}" data-review-search="${escapeAttr(searchable.toLowerCase())}">
              <div class="review-turn-label">${turnNum}<span class="review-type-badge type-${reviewType}" data-test="review-type-${t.turn || 0}">${EVENT_TYPE_LABELS[reviewType]}</span></div>
              <div class="review-bubble review-player">${playerBubble}</div>
              <div class="review-bubble review-gm">${narration}</div>
            </div>`;
          }).join("");
          // Prepend older turns before existing ones
          while (tempDiv.firstChild) {
            timeline.insertBefore(tempDiv.firstChild, timeline.firstChild);
          }
          // Update load-more button
          const loadMoreContainer = body.querySelector('[data-test="review-load-more"]');
          if (loadMoreContainer) {
            if (data.has_more) {
              const totalLoaded = existingChapters + data.turns.length;
              loadMoreBtn.textContent = `加载更早回合 (已加载 ${totalLoaded}/${data.total})`;
              loadMoreBtn.disabled = false;
            } else {
              loadMoreContainer.innerHTML = `<div class="review-load-info">已加载全部 ${data.total} 个回合</div>`;
            }
          }
          // Update filter count
          const countEl = body.querySelector('[data-test="review-filter-count"]');
          if (countEl) {
            const allChapters = body.querySelectorAll("[data-review-chapter]");
            countEl.textContent = `共 ${allChapters.length} 个回合`;
          }
        } else {
          const loadMoreContainer = body.querySelector('[data-test="review-load-more"]');
          if (loadMoreContainer) {
            loadMoreContainer.innerHTML = `<div class="review-load-info">已加载全部回合</div>`;
          }
        }
      } catch (e) {
        loadMoreBtn.textContent = "加载失败,点击重试";
        loadMoreBtn.disabled = false;
      }
    });
  }
}

function renderReviewTypeFilters(turns) {
  const counts = turns.reduce((acc, turn) => {
    const type = detectReviewTurnType(turn);
    acc[type] = (acc[type] || 0) + 1;
    acc.all += 1;
    return acc;
  }, { all: 0 });
  return `<div class="review-type-filters" data-test="review-type-filters">${EVENT_TYPE_FILTERS.map((type) => {
    const count = counts[type] || 0;
    const disabled = type !== "all" && count === 0;
    return `<button type="button" class="review-type-filter ${type === 'all' ? 'active' : ''}" data-review-type-filter="${type}" data-test="review-type-filter-${type}" ${disabled ? 'disabled' : ''}>${EVENT_TYPE_LABELS[type]} ${count}</button>`;
  }).join("")}</div>`;
}

function detectReviewTurnType(turn) {
  const text = `${turn.player_input || ""} ${turn.narration || ""}`.toLowerCase();
  if (/战斗|攻击|受伤|伤害|combat|attack|damage|打一拳/.test(text)) return "combat";
  if (/交易|买|卖|钱|雇|purchase|trade/.test(text)) return "trade";
  if (/请教|询问|闲谈|说服|顾问|social/.test(text)) return "social";
  if (/线索|剧情|状纸|证据|结局|plot|clue|ending/.test(text)) return "plot";
  return "test";
}

function applyReviewFilter(body) {
  const input = body.querySelector('[data-test="review-filter-input"]');
  const countEl = body.querySelector('[data-test="review-filter-count"]');
  const emptyEl = body.querySelector('[data-test="review-filter-empty"]');
  const matchControls = body.querySelector('[data-review-match-controls]');
  const matchIndex = body.querySelector('[data-review-match-index]');
  const activeType = body.querySelector("[data-review-type-filter].active")?.dataset.reviewTypeFilter || "all";
  const chapters = Array.from(body.querySelectorAll("[data-review-chapter]"));
  const query = (input?.value || "").trim().toLowerCase();
  let matched = 0;
  chapters.forEach((chapter) => {
    const textMatch = !query || (chapter.dataset.reviewSearch || "").includes(query);
    const typeMatch = activeType === "all" || chapter.dataset.reviewType === activeType;
    const isMatch = textMatch && typeMatch;
    if (!isMatch) chapter.classList.remove("review-match-current");
    chapter.classList.toggle("review-hidden", !isMatch);
    if (isMatch) matched += 1;
  });
  if (countEl) {
    const typePrefix = activeType === "all" ? "" : `${EVENT_TYPE_LABELS[activeType]} · `;
    countEl.textContent = (query || activeType !== "all")
      ? `${typePrefix}匹配 ${matched} / ${chapters.length} 个回合`
      : `共 ${chapters.length} 个回合`;
  }
  if (emptyEl) emptyEl.classList.toggle("hidden", !(query || activeType !== "all") || matched > 0);

  // Update match navigation controls
  const visible = chapters.filter((ch) => !ch.classList.contains("review-hidden"));
  if (matchControls) matchControls.classList.toggle("hidden", matched === 0 || !(query || activeType !== "all"));
  if (matchIndex && visible.length > 0) {
    const currentIdx = visible.findIndex((ch) => ch.classList.contains("review-match-current"));
    const idx = currentIdx >= 0 ? currentIdx + 1 : 1;
    matchIndex.textContent = `${idx} / ${visible.length}`;
  } else if (matchIndex) {
    matchIndex.textContent = "0 / 0";
  }
  // Ensure first match is marked if none marked
  if (visible.length > 0 && !visible.some((ch) => ch.classList.contains("review-match-current"))) {
    visible[0].classList.add("review-match-current");
    visible[0].scrollIntoView({ behavior: "smooth", block: "start" });
    if (matchIndex) matchIndex.textContent = `1 / ${visible.length}`;
  }
}

function clearReviewFilter(body) {
  const input = body.querySelector('[data-test="review-filter-input"]');
  if (input) input.value = "";
  body.querySelectorAll("[data-review-type-filter]").forEach((el) => {
    el.classList.toggle("active", el.dataset.reviewTypeFilter === "all");
  });
  body.querySelectorAll(".review-match-current").forEach((el) => el.classList.remove("review-match-current"));
  applyReviewFilter(body);
}

function jumpReviewMatch(body, direction) {
  const matches = Array.from(body.querySelectorAll("[data-review-chapter]:not(.review-hidden)"));
  if (matches.length === 0) return;
  let current = matches.findIndex((chapter) => chapter.classList.contains("review-match-current"));
  if (current === -1) current = 0;
  const next = direction === "prev"
    ? (current - 1 + matches.length) % matches.length
    : (current + 1) % matches.length;
  matches.forEach((chapter) => chapter.classList.remove("review-match-current"));
  matches[next].classList.add("review-match-current");
  matches[next].scrollIntoView({ behavior: "smooth", block: "start" });
  const matchIndex = body.querySelector('[data-review-match-index]');
  if (matchIndex) matchIndex.textContent = `${next + 1} / ${matches.length}`;
}
// ===================================================================
// Replay player (可视化回放事件溯源存档)
// ===================================================================
let replayData = null;
let replayCurrentTurn = -1; // -1 = initial state

async function loadReplayPlayer() {
  const modal = $("#replay-modal");
  const body = $("#replay-body");
  body.innerHTML = "<em>加载回放数据...</em>";
  modal.classList.remove("hidden");
  try {
    replayData = await api("/api/save/replay/player");
    replayCurrentTurn = -1;
    body.innerHTML = renderReplayPlayer(replayData);
    bindReplayEvents(body);
    updateReplayView(body);
  } catch (e) {
    replayData = null;
    body.innerHTML = `<em>加载失败: ${escapeHtml(e.message)}</em>`;
  }
}

function classifyReplayTurn(turnData) {
  if (!turnData || !turnData.writes || !turnData.writes.length) return "other";
  const tools = turnData.writes.map((w) => w.tool || "");
  if (tools.some((t) => t.includes("damage") || t.includes("status") || t === "tick_statuses")) return "combat";
  if (tools.some((t) => t.includes("advisor") || t.includes("party") || t.includes("learn"))) return "social";
  if (tools.some((t) => t.includes("clue") || t.includes("ending") || t.includes("quest") || t.includes("evolution"))) return "story";
  if (tools.some((t) => t.includes("money") || t.includes("purchase") || t.includes("hire") || t.includes("transfer"))) return "trade";
  return "other";
}

function computeReplayDiff(prev, curr) {
  if (!prev || !curr) return [];
  const diffs = [];
  const prevEntities = (prev.entities || []);
  const currEntities = (curr.entities || []);

  // Entity changes
  const prevMap = new Map(prevEntities.map((e) => [e.id, e]));
  const currMap = new Map(currEntities.map((e) => [e.id, e]));
  for (const [id, ce] of currMap) {
    const pe = prevMap.get(id);
    if (!pe) { diffs.push({ type: "add", text: `新增实体: ${ce.name || id}` }); continue; }
    // HP change
    const pHp = (pe.attributes || {}).hp;
    const cHp = (ce.attributes || {}).hp;
    if (pHp !== undefined && cHp !== undefined && pHp !== cHp) {
      const d = cHp - pHp;
      diffs.push({ type: d > 0 ? "add" : "remove", text: `${ce.name || id} HP ${d > 0 ? "+" : ""}${d} (${pHp}→${cHp})` });
    }
    // Money change
    const pMoney = (pe.attributes || {}).money_wen;
    const cMoney = (ce.attributes || {}).money_wen;
    if (pMoney !== undefined && cMoney !== undefined && pMoney !== cMoney) {
      const d = cMoney - pMoney;
      diffs.push({ type: d > 0 ? "add" : "remove", text: `${ce.name || id} 钱 ${d > 0 ? "+" : ""}${d}文 (${pMoney}→${cMoney})` });
    }
    // Location change
    if (pe.location !== ce.location) {
      diffs.push({ type: "change", text: `${ce.name || id} 移动 ${pe.location}→${ce.location}` });
    }
    // Status changes
    const pStatuses = (pe.statuses || []).map((s) => s.id || s).sort();
    const cStatuses = (ce.statuses || []).map((s) => s.id || s).sort();
    const added = cStatuses.filter((s) => !pStatuses.includes(s));
    const removed = pStatuses.filter((s) => !cStatuses.includes(s));
    for (const s of added) diffs.push({ type: "add", text: `${ce.name || id} +状态:${s}` });
    for (const s of removed) diffs.push({ type: "remove", text: `${ce.name || id} -状态:${s}` });
  }

  // Flag changes
  const pFlags = prev.flags || {};
  const cFlags = curr.flags || {};
  for (const [k, v] of Object.entries(cFlags)) {
    if (JSON.stringify(pFlags[k]) !== JSON.stringify(v)) {
      diffs.push({ type: "change", text: `标记 ${k} 已更新` });
    }
  }

  // New events
  const pEventCount = (prev.events || []).length;
  const cEventCount = (curr.events || []).length;
  if (cEventCount > pEventCount) {
    const newEvents = (curr.events || []).slice(pEventCount);
    for (const ev of newEvents) {
      diffs.push({ type: "add", text: `事件: ${ev.summary || ev.type || "?"}` });
    }
  }

  // Clue changes
  const pClues = (prev.story_progress || []).length;
  const cClues = (curr.story_progress || []).length;
  if (cClues > pClues) {
    diffs.push({ type: "add", text: `+${cClues - pClues} 条新线索` });
  }

  return diffs;
}

function renderReplayPlayer(data) {
  const total = data.total_turns || 0;
  // Build timeline markers
  let timelineHtml = '<div class="replay-timeline" data-test="replay-timeline" data-replay-timeline>';
  timelineHtml += `<div class="replay-timeline-marker type-other active" data-replay-turn="-1" title="初始状态"></div>`;
  for (let i = 0; i < total; i++) {
    const turnData = data.turns[i];
    const type = classifyReplayTurn(turnData);
    timelineHtml += `<div class="replay-timeline-marker type-${type}" data-replay-turn="${i}" title="回合 ${i + 1}"></div>`;
  }
  timelineHtml += '</div>';
  timelineHtml += `<div class="replay-timeline-legend" data-test="replay-timeline-legend">
    <span class="leg-combat">战斗</span>
    <span class="leg-social">社交</span>
    <span class="leg-story">剧情</span>
    <span class="leg-trade">交易</span>
    <span class="leg-other">其他</span>
  </div>`;

  return `<div class="replay-layout" data-test="replay-layout">
    <div class="replay-header" data-test="replay-header">
      <div class="replay-summary">
        <span><strong>${total}</strong> 回合</span>
        <span data-replay-turn-label>初始状态</span>
      </div>
      <div class="replay-controls" data-test="replay-controls">
        <button type="button" data-replay-nav="start" data-test="replay-nav-start" title="回到起点 (Home)">⏮</button>
        <button type="button" data-replay-nav="prev" data-test="replay-nav-prev" title="上一回合 (←)">◀</button>
        <button type="button" data-replay-nav="play" data-test="replay-nav-play" title="自动播放 (Space)">▶</button>
        <button type="button" data-replay-nav="next" data-test="replay-nav-next" title="下一回合 (→)">▶</button>
        <button type="button" data-replay-nav="end" data-test="replay-nav-end" title="跳到末尾 (End)">⏭</button>
        <div class="replay-speed" data-test="replay-speed">
          <label>速度:</label>
          <select data-replay-speed-select data-test="replay-speed-select">
            <option value="4000">0.5x</option>
            <option value="2000" selected>1x</option>
            <option value="1000">2x</option>
            <option value="500">4x</option>
          </select>
        </div>
      </div>
    </div>
    ${timelineHtml}
    <div class="replay-scrubber" data-test="replay-scrubber">
      <input type="range" min="-1" max="${total - 1}" value="-1" data-replay-slider data-test="replay-slider" />
      <div class="replay-scrubber-labels">
        <span>初始</span>
        <span data-replay-slider-value>初始状态</span>
        <span>回合 ${total}</span>
      </div>
    </div>
    <div class="replay-content" data-test="replay-content">
      <div class="replay-turn-dialog" data-test="replay-dialog">
        <div class="replay-player-bubble" data-replay-player-input data-test="replay-player-input">—</div>
        <div class="replay-gm-bubble" data-replay-narration data-test="replay-narration">等待播放...</div>
        <div class="replay-writes" data-replay-writes data-test="replay-writes"></div>
        <div class="replay-diff hidden" data-replay-diff data-test="replay-diff">
          <div class="replay-diff-title">状态变化</div>
          <div data-replay-diff-list></div>
        </div>
      </div>
      <div class="replay-world-state" data-test="replay-world-state">
        <div class="replay-state-section" data-test="replay-state-player">
          <h4>玩家</h4>
          <div data-replay-state-player>—</div>
        </div>
        <div class="replay-state-section" data-test="replay-state-location">
          <h4>场景</h4>
          <div data-replay-state-location>—</div>
        </div>
        <div class="replay-state-section" data-test="replay-state-nearby">
          <h4>附近</h4>
          <div data-replay-state-nearby>—</div>
        </div>
        <div class="replay-state-section" data-test="replay-state-events">
          <h4>近期事件</h4>
          <div data-replay-state-events>—</div>
        </div>
        <div class="replay-state-section" data-test="replay-state-time">
          <h4>时间</h4>
          <div data-replay-state-time>—</div>
        </div>
      </div>
    </div>
    <div class="replay-kbd-hint" data-test="replay-kbd-hint">快捷键: ← → 切换回合 | Space 播放/暂停 | Home End 跳转</div>
  </div>`;
}

function updateReplayView(body) {
  if (!replayData) return;
  const total = replayData.total_turns || 0;
  const isInitial = replayCurrentTurn < 0;
  const turnData = isInitial ? null : replayData.turns[replayCurrentTurn];
  const state = isInitial ? replayData.initial_state : turnData.state;

  // Update turn label
  const label = body.querySelector("[data-replay-turn-label]");
  if (label) label.textContent = isInitial ? "初始状态" : `回合 ${replayCurrentTurn + 1} / ${total}`;

  // Update timeline markers
  const timeline = body.querySelector("[data-replay-timeline]");
  if (timeline) {
    timeline.querySelectorAll(".replay-timeline-marker").forEach((m) => {
      const turnIdx = parseInt(m.dataset.replayTurn, 10);
      m.classList.toggle("active", turnIdx === replayCurrentTurn);
    });
  }

  // Update slider
  const slider = body.querySelector("[data-replay-slider]");
  if (slider) slider.value = replayCurrentTurn;
  const sliderValue = body.querySelector("[data-replay-slider-value]");
  if (sliderValue) sliderValue.textContent = isInitial ? "初始状态" : `回合 ${replayCurrentTurn + 1}`;

  // Update dialog bubbles
  const playerInput = body.querySelector("[data-replay-player-input]");
  const narration = body.querySelector("[data-replay-narration]");
  const writes = body.querySelector("[data-replay-writes]");
  if (playerInput) playerInput.textContent = isInitial ? "(世界初始状态)" : (turnData.player_input || "—");
  if (narration) {
    if (isInitial) {
      narration.textContent = "这是游戏开始前的世界状态。使用下方控制按钮或滑块逐步回放。";
    } else {
      narration.textContent = turnData.narration || "—";
    }
  }
  if (writes) {
    if (isInitial || !turnData.writes.length) {
      writes.innerHTML = "";
    } else {
      writes.innerHTML = `<div class="replay-write-list">${turnData.writes.map(
        (w) => `<span class="replay-write-tag">${escapeHtml(w.summary || w.tool)}</span>`
      ).join("")}</div>`;
    }
  }

  // Update diff panel
  const diffPanel = body.querySelector("[data-replay-diff]");
  const diffList = body.querySelector("[data-replay-diff-list]");
  if (diffPanel && diffList) {
    if (isInitial) {
      diffPanel.classList.add("hidden");
    } else {
      const prevState = replayCurrentTurn > 0
        ? replayData.turns[replayCurrentTurn - 1].state
        : replayData.initial_state;
      const diffs = computeReplayDiff(prevState, state);
      if (diffs.length) {
        diffPanel.classList.remove("hidden");
        diffList.innerHTML = diffs.slice(0, 20).map((d) =>
          `<div class="replay-diff-item diff-${d.type}">${escapeHtml(d.text)}</div>`
        ).join("") + (diffs.length > 20 ? `<div class="replay-diff-item">...还有 ${diffs.length - 20} 项变化</div>` : "");
      } else {
        diffPanel.classList.add("hidden");
      }
    }
  }

  // Update world state panels
  const entities = state.entities || [];
  const locations = state.locations || [];
  const events = state.events || [];
  const player = entities.find((e) => e.id === "player");
  const playerLocation = player ? player.location : null;
  const currentLoc = locations.find((l) => l.id === playerLocation);
  const nearby = entities.filter((e) => e.id !== "player" && e.location === playerLocation);

  const playerPanel = body.querySelector("[data-replay-state-player]");
  if (playerPanel) {
    if (player) {
      const attrs = player.attributes || {};
      const hp = attrs.hp ?? "?";
      const maxHp = attrs.max_hp ?? "?";
      const money = attrs.money_wen ?? 0;
      playerPanel.innerHTML = `<div class="replay-entity-card">
        <strong>${escapeHtml(player.name || player.id)}</strong>
        <span>HP: ${hp}/${maxHp}</span>
        <span>钱: ${money}文</span>
        ${player.statuses && player.statuses.length ? `<span>状态: ${player.statuses.map((s) => escapeHtml(s.id || s)).join(", ")}</span>` : ""}
      </div>`;
    } else {
      playerPanel.innerHTML = "<em>无玩家数据</em>";
    }
  }

  const locationPanel = body.querySelector("[data-replay-state-location]");
  if (locationPanel) {
    if (currentLoc) {
      locationPanel.innerHTML = `<div class="replay-loc-card">
        <strong>${escapeHtml(currentLoc.name || currentLoc.id)}</strong>
        <span>${escapeHtml(currentLoc.description || "")}</span>
      </div>`;
    } else {
      locationPanel.innerHTML = "<em>未知位置</em>";
    }
  }

  const nearbyPanel = body.querySelector("[data-replay-state-nearby]");
  if (nearbyPanel) {
    if (nearby.length) {
      nearbyPanel.innerHTML = nearby.map((npc) => {
        const attrs = npc.attributes || {};
        return `<div class="replay-npc-card">
          <strong>${escapeHtml(npc.name || npc.id)}</strong>
          ${attrs.hp !== undefined ? `<span>HP:${attrs.hp}/${attrs.max_hp || "?"}</span>` : ""}
        </div>`;
      }).join("");
    } else {
      nearbyPanel.innerHTML = "<em>无人在场</em>";
    }
  }

  const eventsPanel = body.querySelector("[data-replay-state-events]");
  if (eventsPanel) {
    const recentEvents = events.slice(-5);
    if (recentEvents.length) {
      eventsPanel.innerHTML = recentEvents.map(
        (ev) => `<div class="replay-event-item"><span class="replay-event-type">${escapeHtml(ev.type || "?")}</span> ${escapeHtml(ev.summary || "")}</div>`
      ).join("");
    } else {
      eventsPanel.innerHTML = "<em>暂无事件</em>";
    }
  }

  const timePanel = body.querySelector("[data-replay-state-time]");
  if (timePanel) {
    const time = state.time || {};
    timePanel.innerHTML = `<span>第${time.day_index ?? "?"}天 · ${time.period ?? "?"}</span>`;
  }
}

function replayNav(body, action) {
  if (!replayData) return;
  const total = replayData.total_turns || 0;
  if (action === "start") replayCurrentTurn = -1;
  else if (action === "end") replayCurrentTurn = total - 1;
  else if (action === "prev") replayCurrentTurn = Math.max(-1, replayCurrentTurn - 1);
  else if (action === "next") replayCurrentTurn = Math.min(total - 1, replayCurrentTurn + 1);
  updateReplayView(body);
}

function bindReplayEvents(body) {
  // Navigation buttons
  body.querySelectorAll("[data-replay-nav]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const action = btn.dataset.replayNav;
      if (action === "play") {
        toggleReplayAutoPlay(body, btn);
        return;
      }
      replayNav(body, action);
    });
  });

  // Timeline markers
  body.querySelectorAll("[data-replay-turn]").forEach((marker) => {
    marker.addEventListener("click", () => {
      replayCurrentTurn = parseInt(marker.dataset.replayTurn, 10);
      updateReplayView(body);
    });
  });

  // Slider
  const slider = body.querySelector("[data-replay-slider]");
  if (slider) {
    slider.addEventListener("input", () => {
      replayCurrentTurn = parseInt(slider.value, 10);
      updateReplayView(body);
    });
  }

  // Speed control
  const speedSelect = body.querySelector("[data-replay-speed-select]");
  if (speedSelect) {
    speedSelect.addEventListener("change", () => {
      replayAutoPlayInterval = parseInt(speedSelect.value, 10);
      // If currently playing, restart with new speed
      if (replayAutoPlayTimer) {
        const playBtn = body.querySelector('[data-replay-nav="play"]');
        stopReplayAutoPlay(playBtn);
        startReplayAutoPlay(body, playBtn);
      }
    });
  }

  // Keyboard shortcuts
  replayKeyHandler = (e) => {
    if (!replayData) return;
    // Don't intercept when typing in inputs
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.tagName === "SELECT") return;
    if (e.key === "ArrowLeft") { e.preventDefault(); replayNav(body, "prev"); }
    else if (e.key === "ArrowRight") { e.preventDefault(); replayNav(body, "next"); }
    else if (e.key === "Home") { e.preventDefault(); replayNav(body, "start"); }
    else if (e.key === "End") { e.preventDefault(); replayNav(body, "end"); }
    else if (e.key === " ") {
      e.preventDefault();
      const playBtn = body.querySelector('[data-replay-nav="play"]');
      if (playBtn) toggleReplayAutoPlay(body, playBtn);
    }
  };
  document.addEventListener("keydown", replayKeyHandler);
}

let replayAutoPlayTimer = null;
let replayAutoPlayInterval = 2000;
let replayKeyHandler = null;

function stopReplayAutoPlay(playBtn) {
  if (replayAutoPlayTimer) {
    clearInterval(replayAutoPlayTimer);
    replayAutoPlayTimer = null;
  }
  if (playBtn) {
    playBtn.textContent = "▶";
    playBtn.title = "自动播放 (Space)";
  }
}

function startReplayAutoPlay(body, playBtn) {
  if (playBtn) {
    playBtn.textContent = "⏸";
    playBtn.title = "暂停 (Space)";
  }
  const total = replayData ? replayData.total_turns : 0;
  replayAutoPlayTimer = setInterval(() => {
    if (replayCurrentTurn >= total - 1) {
      stopReplayAutoPlay(playBtn);
      return;
    }
    replayCurrentTurn += 1;
    updateReplayView(body);
  }, replayAutoPlayInterval);
}

function toggleReplayAutoPlay(body, btn) {
  if (replayAutoPlayTimer) {
    stopReplayAutoPlay(btn);
    return;
  }
  startReplayAutoPlay(body, btn);
}
// ===================================================================
function renderBirthModal(templates, selectedId) {
  if (!templates.length) return "<em>暂无出生模板</em>";
  const selected = templates.find((t) => t.id === selectedId) || templates[0];
  const currentId = ((lastSidePanelState || {}).flags || {}).birth_setting?.template_id || "scholar";
  return `<div class="birth-quick-switch" data-test="birth-quick-switch">
    <div class="birth-current">当前出生: <strong>${escapeHtml(selectedBirthTemplateName(currentId))}</strong></div>
    <div class="birth-quick-actions">
      ${templates.map((t) => `<button type="button" class="birth-quick-option ${t.id === currentId ? 'active' : ''}" data-birth-quick="${escapeAttr(t.id)}" data-test="birth-quick-${escapeAttr(t.id)}">
        ${escapeHtml(t.name)}
      </button>`).join("")}
    </div>
  </div>
  <div class="birth-layout">
    <div class="birth-template-list" data-test="birth-template-list">
      ${templates.map((t) => `<button type="button" class="birth-template-option ${t.id === selected.id ? 'active' : ''}" data-birth-template="${escapeAttr(t.id)}" data-test="birth-template-${escapeAttr(t.id)}">
        <strong>${escapeHtml(t.name)}</strong>
        <span>${escapeHtml(t.summary || '')}</span>
      </button>`).join("")}
    </div>
    <div class="birth-template-detail" data-test="birth-template-detail">
      ${renderBirthTemplateDetail(selected)}
      <button type="button" class="birth-apply" data-birth-apply="${escapeAttr(selected.id)}" data-test="apply-birth-template">以此出生开始</button>
    </div>
  </div>`;
}

function renderBirthTemplateDetail(t) {
  const attrs = t.attributes || {};
  const skills = Object.entries(attrs.skills || {})
    .map(([id, s]) => `<span>${escapeHtml(s.name || id)} Lv.${s.level ?? 0}</span>`)
    .join("") || "<em>无</em>";
  const inventory = (t.inventory || [])
    .map((i) => `${i.name || i.id}${i.qty ? `×${i.qty}` : ''}`)
    .join("、") || "无";
  const start = t.start || {};
  return `<div class="birth-detail-card">
    <h3>${escapeHtml(t.name)}</h3>
    <p>${escapeHtml(t.summary || '')}</p>
    <div class="birth-stat-grid">
      <div><span>身份</span>${escapeHtml(attrs.social_identity || attrs.occupation || '')}</div>
      <div><span>出身</span>${escapeHtml(attrs.family_background || attrs.origin || '')}</div>
      <div><span>HP</span>${attrs.hp ?? '?'} / ${attrs.max_hp ?? '?'}</div>
      <div><span>钱</span>${attrs.money_wen ?? 0} 文</div>
      <div><span>攻防</span>${attrs.attack ?? 0} / ${attrs.defense ?? 0}</div>
      <div><span>观察</span>${attrs.observation ?? 0}</div>
    </div>
    <div class="birth-row"><strong>技能</strong><div class="birth-skills">${skills}</div></div>
    <div class="birth-row"><strong>初始物品</strong>${escapeHtml(inventory)}</div>
    <div class="birth-row"><strong>起点</strong>${escapeHtml(start.location || '')} @ [${(start.pos || []).join(',')}]</div>
  </div>`;
}

function bindBirthModalEvents() {
  const body = $("#birth-body");
  body.querySelectorAll("[data-birth-template]").forEach((btn) => {
    btn.addEventListener("click", () => {
      selectedBirthTemplateId = btn.dataset.birthTemplate;
      body.innerHTML = renderBirthModal(birthTemplates, selectedBirthTemplateId);
      bindBirthModalEvents();
    });
  });
  body.querySelectorAll("[data-birth-quick]").forEach((btn) => {
    btn.addEventListener("click", () => applyBirthTemplateFromModal(btn.dataset.birthQuick, btn));
  });
  const applyBtn = body.querySelector("[data-birth-apply]");
  if (applyBtn) {
    applyBtn.addEventListener("click", () => applyBirthTemplateFromModal(applyBtn.dataset.birthApply, applyBtn));
  }
}

async function applyBirthTemplateFromModal(templateId, button) {
  button.disabled = true;
  const oldText = button.textContent;
  button.textContent = "应用中...";
  try {
    const res = await api("/api/reset?template_id=" + encodeURIComponent(templateId), { method: "POST" });
    selectedBirthTemplateId = templateId;
    chat.innerHTML = "";
    addBubble("system", `已选择「${selectedBirthTemplateName(templateId)}」出生。世界已重置。`);
    showOpeningForState(res.state);
    renderSidePanel(res.state);
    renderScene(res.state);
    $("#birth-modal").classList.add("hidden");
  } catch (e) {
    addBubble("system", `应用出生设置失败: ${e.message}`);
    button.disabled = false;
    button.textContent = oldText;
  }
}

function selectedBirthTemplateName(templateId) {
  const template = birthTemplates.find((t) => t.id === templateId);
  return template ? template.name : templateId;
}

async function openBirthModal() {
  const modal = $("#birth-modal");
  const body = $("#birth-body");
  body.innerHTML = "<em>加载中...</em>";
  modal.classList.remove("hidden");
  try {
    const data = await api("/api/birth/templates");
    const summaries = data.templates || [];
    birthTemplates = await Promise.all(summaries.map((t) => api("/api/birth/templates/" + encodeURIComponent(t.id))));
    if (!selectedBirthTemplateId && lastSidePanelState) {
      selectedBirthTemplateId = ((lastSidePanelState.flags || {}).birth_setting || {}).template_id;
    }
    selectedBirthTemplateId = selectedBirthTemplateId || (birthTemplates.find((t) => t.id === "scholar") || birthTemplates[0] || {}).id;
    body.innerHTML = renderBirthModal(birthTemplates, selectedBirthTemplateId);
    bindBirthModalEvents();
  } catch (e) {
    body.innerHTML = `<em>加载失败: ${escapeHtml(e.message)}</em>`;
  }
}

function renderAudit(turns) {
  if (!turns.length) return "<em>暂无记录</em>";
  return turns.slice().reverse().map((t) => {
    const tools = (t.agent_trace || [])
      .filter((s) => s.type === "tool_use")
      .map((s) => `<div class="audit-tool">
        → ${s.name}(${JSON.stringify(s.input)})
      </div>`).join("");
    const laws = (t.cited_laws || []).length
      ? `<div class="laws">引法条: ${t.cited_laws.join(", ")}</div>` : "";
    return `<div class="audit-turn">
      <h4>Turn ${t.turn} · ${escapeHtml(t.player_input)}</h4>
      ${tools}
      ${laws}
      <div class="narration">${escapeHtml(t.narration || "")}</div>
    </div>`;
  }).join("");
}

function renderDebugConsole(data) {
  const world = data.world || {};
  const audit = data.audit || {};
  const perf = data.performance || {};
  const player = world.player || {};
  const loc = world.current_location || {};
  const tools = audit.recent_tool_calls || [];
  const toolNames = audit.tool_names || [];
  return `<div class="debug-grid" data-test="debug-summary">
    <div><span>实体</span><strong>${world.entity_count ?? 0}</strong></div>
    <div><span>地点</span><strong>${world.location_count ?? 0}</strong></div>
    <div><span>事件窗口</span><strong>${world.event_count ?? 0}</strong></div>
    <div><span>Flags</span><strong>${world.flag_count ?? 0}</strong></div>
    <div><span>审计回合</span><strong>${audit.turn_count ?? 0}</strong></div>
    <div><span>审计大小</span><strong>${perf.audit_bytes ?? 0} B</strong></div>
  </div>
  <div class="debug-export" data-test="debug-export">
    <button type="button" data-test="debug-export-bundle">导出调试包</button>
    <span>包含当前世界摘要、实体/flag、筛选后的工具调用与性能指标</span>
  </div>
  <div class="debug-section" data-test="debug-world-state">
    <h3>世界状态查看器</h3>
    <div class="debug-row"><strong>玩家</strong>${escapeHtml(player.name || player.id || '无')} @ ${escapeHtml(player.location || '未知')}</div>
    <div class="debug-row"><strong>地点</strong>${escapeHtml(loc.name || loc.id || '未知')}</div>
    <div class="debug-row"><strong>时间</strong>${escapeHtml(Object.values(world.time || {}).filter(Boolean).join(' ') || '未知')}</div>
  </div>
  ${renderDebugTestPresets(debugTestPresets)}
  ${renderDebugTestSnapshots(debugTestSnapshots, debugTestSnapshotSummary)}
  ${renderDebugEntityFlagBrowser(world)}
  <div class="debug-section" data-test="debug-tool-log">
    <h3>工具调用日志</h3>
    <div class="debug-tool-filters" data-test="debug-tool-filters">
      <select data-test="debug-tool-name-filter" aria-label="按工具名筛选">
        <option value="">全部工具</option>
        ${toolNames.map((name) => `<option value="${escapeAttr(name)}" ${name === debugToolFilter ? 'selected' : ''}>${escapeHtml(name)}</option>`).join('')}
      </select>
      <input type="search" value="${escapeAttr(debugToolQuery)}" data-test="debug-tool-query-filter" placeholder="筛选输入/输出内容" aria-label="按工具调用内容筛选" />
      <button type="button" data-test="debug-tool-filter-clear">清空</button>
    </div>
    <div class="debug-tool-filter-summary" data-test="debug-tool-filter-summary">匹配 ${audit.filtered_tool_count ?? tools.length} 次调用</div>
    ${tools.length ? tools.slice().reverse().map((tool) => {
      const inputJson = JSON.stringify(tool.input || {}, null, 2);
      const outputJson = JSON.stringify(tool.output || {}, null, 2);
      return `<div class="debug-tool-call" data-test="debug-tool-${escapeAttr(tool.name || 'unknown')}">
        <div><strong>Turn ${tool.turn ?? '?'}</strong> · ${escapeHtml(tool.name || 'unknown')}</div>
        <div class="debug-tool-label-row">
          <label>输入</label>
          <button type="button" data-test="debug-copy-input" data-debug-copy="输入" data-debug-copy-text="${escapeAttr(inputJson)}">复制输入</button>
        </div>
        <pre data-test="debug-tool-input">${escapeHtml(inputJson)}</pre>
        <div class="debug-tool-label-row">
          <label>输出</label>
          <button type="button" data-test="debug-copy-output" data-debug-copy="输出" data-debug-copy-text="${escapeAttr(outputJson)}">复制输出</button>
        </div>
        <pre data-test="debug-tool-output">${escapeHtml(outputJson)}</pre>
      </div>`;
    }).join('') : '<em data-test="debug-tool-empty">暂无匹配工具调用</em>'}
  </div>
  <div class="debug-section" data-test="debug-performance">
    <h3>性能监控</h3>
    <div class="debug-row"><strong>快照事件窗口</strong>${perf.snapshot_event_window ?? 0}</div>
    <div class="debug-row"><strong>渲染统计</strong>draws ${window.__renderSceneStats?.draws ?? 0} / skips ${window.__renderSceneStats?.skips ?? 0}</div>
  </div>`;
}

function renderDebugTestPresets(presets) {
  return `<div class="debug-section" data-test="debug-test-presets">
    <h3>预设测试用例</h3>
    <div data-test="debug-preset-list">
      ${presets.length ? presets.map((preset) => renderDebugTestPresetRow(preset)).join("") : '<em>暂无预设测试用例</em>'}
    </div>
  </div>`;
}

function renderDebugTestPresetRow(preset) {
  return `<div class="debug-snapshot-item debug-preset-item" data-test="debug-preset-${escapeAttr(preset.id)}">
    <div>
      <strong>${escapeHtml(preset.name || preset.id)}</strong>
      <span>${escapeHtml(preset.summary || '')}</span>
      ${(preset.actions || []).length ? `<p>验收点: ${(preset.actions || []).map((action) => escapeHtml(action)).join('；')}</p>` : ''}
    </div>
    <button type="button" data-debug-preset-load="${escapeAttr(preset.id)}" data-test="debug-preset-load-${escapeAttr(preset.id)}">加载预设</button>
  </div>`;
}

function renderDebugTestSnapshots(snapshots, summary = {}) {
  const query = debugSnapshotQuery.trim().toLowerCase();
  const tagFilter = debugSnapshotTagFilter.trim();
  const snapshotTags = Array.from(new Set(snapshots.flatMap((snapshot) => snapshot.tags || []))).sort((a, b) => a.localeCompare(b, "zh-Hans-CN"));
  const activeSnapshots = snapshots.filter((snapshot) => debugSnapshotShowArchived || !snapshot.archived);
  const archivedCount = snapshots.filter((snapshot) => snapshot.archived).length;
  const filteredSnapshots = activeSnapshots.filter((snapshot) => {
    const matchesQuery = !query || debugSnapshotSearchText(snapshot).includes(query);
    const matchesTag = !tagFilter || (snapshot.tags || []).includes(tagFilter);
    return matchesQuery && matchesTag;
  });
  const sortedSnapshots = sortDebugSnapshots(filteredSnapshots);
  const visibleIds = sortedSnapshots.map((snapshot) => snapshot.id).filter(Boolean);
  const selectedVisibleCount = visibleIds.filter((id) => debugSnapshotSelectedIds.has(id)).length;
  const allVisibleSelected = visibleIds.length > 0 && selectedVisibleCount === visibleIds.length;
  const totals = summary.totals || {};
  return `<div class="debug-section" data-test="debug-test-snapshots">
    <h3>测试场景快照</h3>
    <div class="debug-snapshot-summary" data-test="debug-snapshot-summary">
      <span>总数 <strong>${summary.snapshot_count ?? snapshots.length}</strong></span>
      <span>实体 ${totals.entities ?? 0}</span>
      <span>地点 ${totals.locations ?? 0}</span>
      <span>事件 ${totals.events ?? 0}</span>
      <span>Flags ${totals.flags ?? 0}</span>
      <span>最近更新 ${escapeHtml(summary.latest_updated_at || '无')}</span>
      <span>已归档 ${archivedCount}</span>
    </div>
    ${renderDebugSnapshotQuickFilters(snapshots, activeSnapshots, snapshotTags)}
    <div class="debug-snapshot-form">
      <input type="text" data-test="debug-snapshot-name" placeholder="快照名称,如: 府衙初始盘面" aria-label="测试快照名称" />
      <input type="text" data-test="debug-snapshot-note" placeholder="备注(可选)" aria-label="测试快照备注" />
      <input type="text" data-test="debug-snapshot-tags" placeholder="标签(逗号分隔,如: 府衙,回归)" aria-label="测试快照标签" />
      <button type="button" data-test="debug-snapshot-create">保存当前场景</button>
      <button type="button" data-test="debug-snapshot-index-export">导出索引</button>
      <button type="button" data-test="debug-snapshot-health-check">校验快照</button>
      <button type="button" data-test="debug-snapshot-health-export">导出校验报告</button>
      <button type="button" data-test="debug-snapshot-import-file">导入快照文件</button>
      <button type="button" data-test="debug-snapshot-bundle-import-file">预览快照包</button>
      <input type="file" accept="application/json" hidden data-test="debug-snapshot-file-input" />
      <input type="file" accept="application/json" hidden data-test="debug-snapshot-bundle-file-input" />
    </div>
    ${debugSnapshotBundleImportPreview ? renderDebugSnapshotBundleImportPreview(debugSnapshotBundleImportPreview) : ''}
    ${debugSnapshotHealth ? renderDebugSnapshotHealth(debugSnapshotHealth) : ''}
    <div class="debug-snapshot-filter">
      <input type="search" value="${escapeAttr(debugSnapshotQuery)}" data-test="debug-snapshot-filter" placeholder="筛选快照名称 / 备注 / id / 标签" aria-label="筛选测试快照" />
      <select data-test="debug-snapshot-tag-filter" aria-label="按标签筛选测试快照">
        <option value="" ${tagFilter ? "" : "selected"}>全部标签</option>
        ${snapshotTags.map((tag) => `<option value="${escapeAttr(tag)}" ${tagFilter === tag ? "selected" : ""}>${escapeHtml(tag)}</option>`).join("")}
      </select>
      <select data-test="debug-snapshot-sort" aria-label="测试快照排序">
        <option value="updated_desc" ${debugSnapshotSort === "updated_desc" ? "selected" : ""}>置顶 + 最近更新</option>
        <option value="created_desc" ${debugSnapshotSort === "created_desc" ? "selected" : ""}>置顶 + 最近创建</option>
        <option value="name_asc" ${debugSnapshotSort === "name_asc" ? "selected" : ""}>名称 A→Z</option>
        <option value="name_desc" ${debugSnapshotSort === "name_desc" ? "selected" : ""}>名称 Z→A</option>
      </select>
      <label class="debug-snapshot-archive-toggle"><input type="checkbox" data-test="debug-snapshot-show-archived" ${debugSnapshotShowArchived ? "checked" : ""} /> 显示归档</label>
      <span data-test="debug-snapshot-filter-count">${query || tagFilter || debugSnapshotShowArchived ? `匹配 ${sortedSnapshots.length} / ${snapshots.length} 个快照` : `显示 ${activeSnapshots.length} / ${snapshots.length} 个快照`}</span>
      ${query || tagFilter ? '<button type="button" data-test="debug-snapshot-filter-clear">清空</button>' : ''}
    </div>
    <div class="debug-snapshot-bulk" data-test="debug-snapshot-bulk-actions">
      <label><input type="checkbox" data-test="debug-snapshot-select-visible" ${allVisibleSelected ? "checked" : ""} ${visibleIds.length ? "" : "disabled"} /> 选择当前列表</label>
      <span data-test="debug-snapshot-selected-count">已选 ${debugSnapshotSelectedIds.size} 个</span>
      <button type="button" data-test="debug-snapshot-bulk-export" ${debugSnapshotSelectedIds.size ? "" : "disabled"}>导出所选</button>
      <button type="button" data-test="debug-snapshot-bulk-archive" ${debugSnapshotSelectedIds.size ? "" : "disabled"}>归档所选</button>
      <button type="button" data-test="debug-snapshot-bulk-unarchive" ${debugSnapshotSelectedIds.size ? "" : "disabled"}>取消归档</button>
      <button type="button" class="danger" data-test="debug-snapshot-bulk-delete" ${debugSnapshotSelectedIds.size ? "" : "disabled"}>删除所选</button>
      ${debugSnapshotSelectedIds.size ? '<button type="button" data-test="debug-snapshot-selection-clear">清空选择</button>' : ''}
    </div>
    <div data-test="debug-snapshot-list">
      ${sortedSnapshots.length ? sortedSnapshots.map((snapshot) => renderDebugTestSnapshotRow(snapshot)).join("") : (snapshots.length ? '<em data-test="debug-snapshot-empty">无匹配测试快照</em>' : '<em>暂无测试快照</em>')}
    </div>
  </div>`;
}

function renderDebugSnapshotQuickFilters(snapshots, activeSnapshots, snapshotTags) {
  const pinnedCount = snapshots.filter((snapshot) => snapshot.pinned).length;
  const archivedCount = snapshots.filter((snapshot) => snapshot.archived).length;
  const topTags = snapshotTags.map((tag) => ({ tag, count: snapshots.filter((snapshot) => (snapshot.tags || []).includes(tag)).length }))
    .sort((a, b) => b.count - a.count || a.tag.localeCompare(b.tag, "zh-Hans-CN"))
    .slice(0, 6);
  const activeAll = !debugSnapshotQuery.trim() && !debugSnapshotTagFilter.trim() && !debugSnapshotShowArchived;
  const activePinned = debugSnapshotQuery.trim().toLowerCase() === "pinned";
  const activeArchived = debugSnapshotShowArchived && debugSnapshotQuery.trim().toLowerCase() === "archived";
  return `<div class="debug-snapshot-quick-filters" data-test="debug-snapshot-quick-filters">
    <button type="button" data-debug-snapshot-quick-filter="active" class="${activeAll ? 'active' : ''}" data-test="debug-snapshot-quick-active">当前 ${activeSnapshots.length}</button>
    <button type="button" data-debug-snapshot-quick-filter="all" data-test="debug-snapshot-quick-all">全部 ${snapshots.length}</button>
    <button type="button" data-debug-snapshot-quick-filter="pinned" class="${activePinned ? 'active' : ''}" ${pinnedCount ? '' : 'disabled'} data-test="debug-snapshot-quick-pinned">置顶 ${pinnedCount}</button>
    <button type="button" data-debug-snapshot-quick-filter="archived" class="${activeArchived ? 'active' : ''}" ${archivedCount ? '' : 'disabled'} data-test="debug-snapshot-quick-archived">归档 ${archivedCount}</button>
    ${topTags.map(({ tag, count }) => `<button type="button" data-debug-snapshot-quick-tag="${escapeAttr(tag)}" class="${debugSnapshotTagFilter === tag ? 'active' : ''}" data-test="debug-snapshot-quick-tag-${escapeAttr(tag)}">${escapeHtml(tag)} ${count}</button>`).join('')}
  </div>`;
}

function debugSnapshotSearchText(snapshot) {
  return `${snapshot.id || ""} ${snapshot.name || ""} ${snapshot.note || ""} ${(snapshot.tags || []).join(" ")} ${snapshot.pinned ? "置顶 pinned" : ""} ${snapshot.archived ? "归档 archived" : ""} ${snapshot.created_at || ""} ${snapshot.updated_at || ""} ${snapshot.last_loaded_at || ""} ${snapshot.last_exported_at || ""} ${snapshot.last_imported_at || ""}`.toLowerCase();
}

function parseDebugSnapshotTags(value) {
  const seen = new Set();
  const tags = [];
  for (const rawTag of String(value || "").split(/[，,]/)) {
    const tag = rawTag.trim();
    if (tag && !seen.has(tag)) {
      tags.push(tag);
      seen.add(tag);
    }
  }
  return tags;
}

function sortDebugSnapshots(snapshots) {
  return snapshots.slice().sort((a, b) => {
    if (!!a.pinned !== !!b.pinned) return a.pinned ? -1 : 1;
    if (debugSnapshotSort === "name_asc" || debugSnapshotSort === "name_desc") {
      const result = (a.name || a.id || "").localeCompare(b.name || b.id || "", "zh-Hans-CN");
      return debugSnapshotSort === "name_asc" ? result : -result;
    }
    const field = debugSnapshotSort === "created_desc" ? "created_at" : "updated_at";
    const aTime = a[field] || a.created_at || "";
    const bTime = b[field] || b.created_at || "";
    return String(bTime).localeCompare(String(aTime));
  });
}

function renderDebugSnapshotHealth(health) {
  const issues = health.issues || [];
  return `<div class="debug-snapshot-health ${issues.length ? 'has-issues' : 'ok'}" data-test="debug-snapshot-health-result">
    <div><strong>快照校验</strong><span>${health.ok_count ?? 0} 个正常 / ${health.snapshot_count ?? 0} 个总数 / ${health.issue_count ?? issues.length} 个有问题</span></div>
    ${issues.length ? `<ul>${issues.map((snapshot) => `<li><b>${escapeHtml(snapshot.name || snapshot.id || '未知快照')}</b><span>${escapeHtml((snapshot.issues || []).join('、'))}</span><button type="button" data-debug-health-focus="${escapeAttr(snapshot.id || snapshot.name || '')}" data-test="debug-snapshot-health-focus-${escapeAttr(snapshot.id || snapshot.name || 'unknown')}">定位</button></li>`).join('')}</ul>` : '<em>当前测试快照未发现结构问题。</em>'}
  </div>`;
}

function renderDebugSnapshotBundleImportPreview(preview) {
  const snapshots = preview.snapshots || [];
  const totals = preview.totals || {};
  return `<div class="debug-snapshot-bundle-preview" data-test="debug-snapshot-bundle-preview">
    <div><strong>快照包预览</strong><span>${preview.file_name ? escapeHtml(preview.file_name) : '待导入快照包'} · ${preview.snapshot_count ?? snapshots.length} 个快照 · 实体 ${totals.entities ?? 0} · 地点 ${totals.locations ?? 0} · 事件 ${totals.events ?? 0} · Flags ${totals.flags ?? 0}</span></div>
    <div class="debug-snapshot-bundle-list">
      ${snapshots.slice(0, 5).map((snapshot) => `<p><b>${escapeHtml(snapshot.name || snapshot.id || '未命名快照')}</b><span>${escapeHtml(snapshot.note || '')} · 实体 ${snapshot.entity_count ?? 0} · 事件 ${snapshot.event_count ?? 0} · Flags ${snapshot.flag_count ?? 0}</span></p>`).join('')}
      ${snapshots.length > 5 ? `<em>另有 ${snapshots.length - 5} 个快照未展开</em>` : ''}
    </div>
    <div class="debug-snapshot-confirm-actions">
      <button type="button" data-test="debug-snapshot-bundle-confirm-import">确认导入</button>
      <button type="button" class="secondary" data-test="debug-snapshot-bundle-cancel-import">取消</button>
    </div>
  </div>`;
}

function renderDebugTestSnapshotRow(snapshot) {
  const diff = debugSnapshotDiffs[snapshot.id];
  const detail = debugSnapshotDetails[snapshot.id];
  const confirmation = debugSnapshotLoadConfirmations[snapshot.id];
  const selected = debugSnapshotSelectedIds.has(snapshot.id);
  const activity = [
    snapshot.last_loaded_at ? `加载 ${snapshot.last_loaded_at}` : "",
    snapshot.last_exported_at ? `导出 ${snapshot.last_exported_at}` : "",
    snapshot.last_imported_at ? `导入 ${snapshot.last_imported_at}` : "",
  ].filter(Boolean).join(" · ");
  return `<div class="debug-snapshot-item ${selected ? 'selected' : ''} ${snapshot.pinned ? 'pinned' : ''} ${snapshot.archived ? 'archived' : ''}" data-test="debug-snapshot-${escapeAttr(snapshot.id)}">
    <label class="debug-snapshot-select"><input type="checkbox" data-debug-snapshot-select="${escapeAttr(snapshot.id)}" data-test="debug-snapshot-select-${escapeAttr(snapshot.id)}" ${selected ? "checked" : ""} /> 选择</label>
    <div>
      <strong>${snapshot.pinned ? '<span class="debug-snapshot-pin-badge">置顶</span>' : ''}${snapshot.archived ? '<span class="debug-snapshot-archive-badge">归档</span>' : ''}${escapeHtml(snapshot.name || snapshot.id)}</strong>
      <span>${escapeHtml(snapshot.created_at || '')}${snapshot.updated_at ? ` · 更新 ${escapeHtml(snapshot.updated_at)}` : ''} · 实体 ${snapshot.entity_count ?? 0} · 地点 ${snapshot.location_count ?? 0} · 事件 ${snapshot.event_count ?? 0} · Flags ${snapshot.flag_count ?? 0}</span>
      ${activity ? `<span class="debug-snapshot-activity" data-test="debug-snapshot-activity-${escapeAttr(snapshot.id)}">${escapeHtml(activity)}</span>` : ''}
      ${(snapshot.tags || []).length ? `<div class="debug-snapshot-tags" data-test="debug-snapshot-tags-${escapeAttr(snapshot.id)}">${(snapshot.tags || []).map((tag) => `<span>${escapeHtml(tag)}</span>`).join("")}</div>` : ''}
      ${snapshot.note ? `<p>${escapeHtml(snapshot.note)}</p>` : ''}
      ${confirmation ? renderDebugSnapshotLoadConfirmation(confirmation) : ''}
      ${detail ? renderDebugSnapshotDetail(detail) : ''}
      ${diff ? renderDebugSnapshotDiff(diff) : ''}
    </div>
    <div class="debug-snapshot-actions">
      <button type="button" data-debug-snapshot-load="${escapeAttr(snapshot.id)}" data-test="debug-snapshot-load-${escapeAttr(snapshot.id)}">加载</button>
      <button type="button" data-debug-snapshot-detail="${escapeAttr(snapshot.id)}" data-test="debug-snapshot-detail-${escapeAttr(snapshot.id)}">详情</button>
      <button type="button" data-debug-snapshot-diff="${escapeAttr(snapshot.id)}" data-test="debug-snapshot-diff-${escapeAttr(snapshot.id)}">差异</button>
      <button type="button" data-debug-snapshot-pin="${escapeAttr(snapshot.id)}" data-debug-snapshot-pinned="${snapshot.pinned ? 'true' : 'false'}" data-test="debug-snapshot-pin-${escapeAttr(snapshot.id)}">${snapshot.pinned ? '取消置顶' : '置顶'}</button>
      <button type="button" data-debug-snapshot-archive="${escapeAttr(snapshot.id)}" data-debug-snapshot-archived="${snapshot.archived ? 'true' : 'false'}" data-test="debug-snapshot-archive-${escapeAttr(snapshot.id)}">${snapshot.archived ? '取消归档' : '归档'}</button>
      <button type="button" data-debug-snapshot-duplicate="${escapeAttr(snapshot.id)}" data-debug-snapshot-name="${escapeAttr(snapshot.name || snapshot.id)}" data-test="debug-snapshot-duplicate-${escapeAttr(snapshot.id)}">复制</button>
      <button type="button" data-debug-snapshot-export="${escapeAttr(snapshot.id)}" data-debug-snapshot-name="${escapeAttr(snapshot.name || snapshot.id)}" data-test="debug-snapshot-export-${escapeAttr(snapshot.id)}">导出</button>
      <button type="button" class="danger" data-debug-snapshot-delete="${escapeAttr(snapshot.id)}" data-test="debug-snapshot-delete-${escapeAttr(snapshot.id)}">删除</button>
    </div>
    <div class="debug-snapshot-edit" data-debug-snapshot-edit="${escapeAttr(snapshot.id)}">
      <input type="text" value="${escapeAttr(snapshot.name || snapshot.id)}" aria-label="编辑快照名称" />
      <input type="text" value="${escapeAttr(snapshot.note || '')}" aria-label="编辑快照备注" />
      <input type="text" value="${escapeAttr((snapshot.tags || []).join(', '))}" aria-label="编辑快照标签" />
      <button type="button" data-debug-snapshot-save="${escapeAttr(snapshot.id)}" data-test="debug-snapshot-save-${escapeAttr(snapshot.id)}">保存备注</button>
    </div>
  </div>`;
}

function renderDebugSnapshotLoadConfirmation(detail) {
  const player = detail.player || {};
  const location = detail.current_location || {};
  const events = detail.recent_events || [];
  const latestEvent = events[events.length - 1];
  return `<div class="debug-snapshot-load-confirm" data-test="debug-snapshot-load-confirm">
    <strong>加载确认</strong>
    <span>将恢复「${escapeHtml(detail.name || detail.id)}」: ${escapeHtml(player.name || player.id || '无玩家')} @ ${escapeHtml(location.name || location.id || player.location || '未知地点')}</span>
    <span>包含实体 ${detail.entity_count ?? 0}、事件 ${detail.event_count ?? 0}、Flags ${detail.flag_count ?? 0}${latestEvent ? `；最近事件: ${escapeHtml(latestEvent.summary || latestEvent.type || '未命名事件')}` : ''}</span>
    <div class="debug-snapshot-confirm-actions">
      <button type="button" data-debug-snapshot-confirm-load="${escapeAttr(detail.id)}" data-test="debug-snapshot-confirm-load-${escapeAttr(detail.id)}">确认加载</button>
      <button type="button" class="secondary" data-debug-snapshot-cancel-load="${escapeAttr(detail.id)}" data-test="debug-snapshot-cancel-load-${escapeAttr(detail.id)}">取消</button>
    </div>
  </div>`;
}

function renderDebugSnapshotDetail(detail) {
  const player = detail.player || {};
  const location = detail.current_location || {};
  const flagKeys = detail.flag_keys || [];
  const events = detail.recent_events || [];
  return `<div class="debug-snapshot-detail" data-test="debug-snapshot-detail-result">
    <div><strong>详情预览</strong><span>${escapeHtml(player.name || player.id || '无玩家')} @ ${escapeHtml(location.name || location.id || player.location || '未知地点')}</span></div>
    <p>实体 ${detail.entity_count ?? 0} · 地点 ${detail.location_count ?? 0} · 事件 ${detail.event_count ?? 0} · Flags ${detail.flag_count ?? 0}</p>
    ${flagKeys.length ? `<p><b>Flags</b>${escapeHtml(flagKeys.slice(0, 8).join('、'))}${flagKeys.length > 8 ? '…' : ''}</p>` : ''}
    ${events.length ? `<p><b>最近事件</b>${events.map((event) => escapeHtml(event.summary || event.type || event.id || '未命名事件')).join('；')}</p>` : '<em>该快照暂无事件</em>'}
  </div>`;
}

function renderDebugSnapshotDiff(diff) {
  const summary = diff.summary || {};
  const entities = diff.entities || {};
  const locations = diff.locations || {};
  const flags = diff.flags || {};
  const counts = [
    `实体 +${(entities.added || []).length}/-${(entities.removed || []).length}/改${(entities.changed || []).length}`,
    `地点 +${(locations.added || []).length}/-${(locations.removed || []).length}/改${(locations.changed || []).length}`,
    `Flags +${(flags.added || []).length}/-${(flags.removed || []).length}/改${(flags.changed || []).length}`,
  ];
  const details = [
    renderDebugDiffList("实体变化", entities),
    renderDebugDiffList("地点变化", locations),
    renderDebugDiffList("Flag 变化", flags),
  ].filter(Boolean).join("");
  return `<div class="debug-snapshot-diff" data-test="debug-snapshot-diff-result">
    <div><strong>差异预览</strong><span>${summary.total_changes ?? 0} 类变化 · ${counts.map(escapeHtml).join(' · ')}${summary.events_changed ? ' · 事件不同' : ''}${summary.time_changed ? ' · 时间不同' : ''}</span></div>
    ${details || '<em>当前世界与该快照一致</em>'}
  </div>`;
}

function renderDebugDiffList(title, section) {
  const items = [];
  for (const kind of ["added", "removed", "changed"]) {
    const values = section[kind] || [];
    if (values.length) items.push(`${kind}: ${values.slice(0, 6).join(', ')}${values.length > 6 ? '…' : ''}`);
  }
  if (!items.length) return "";
  return `<p><b>${escapeHtml(title)}</b>${escapeHtml(items.join('；'))}</p>`;
}

function renderDebugEntityFlagBrowser(world) {
  const entities = world.entities || [];
  const flags = world.flags || {};
  const flagEntries = Object.entries(flags);
  return `<div class="debug-section" data-test="debug-entity-flag-browser">
    <h3>实体 / Flag 浏览</h3>
    <input class="debug-filter" type="search" data-test="debug-browser-filter" placeholder="筛选实体、地点、标签或 flag" aria-label="筛选实体和 flag" />
    <div class="debug-browser-columns">
      <div>
        <h4>实体 <span data-test="debug-entity-count">${entities.length}</span></h4>
        <div data-test="debug-entity-list">
          ${entities.map((e) => renderDebugEntityRow(e)).join("") || "<em>暂无实体</em>"}
        </div>
      </div>
      <div>
        <h4>Flags <span data-test="debug-flag-count">${flagEntries.length}</span></h4>
        <div data-test="debug-flag-list">
          ${flagEntries.map(([key, value]) => renderDebugFlagRow(key, value)).join("") || "<em>暂无 Flag</em>"}
        </div>
      </div>
    </div>
    <div class="debug-filter-empty hidden" data-test="debug-browser-empty">无匹配实体或 flag</div>
  </div>`;
}

function renderDebugEntityRow(entity) {
  const attrs = entity.attributes || {};
  const tags = (entity.tags || []).join("、");
  const search = `${entity.id} ${entity.name || ""} ${entity.type || ""} ${entity.location || ""} ${tags} ${attrs.rank || ""} ${attrs.occupation || ""}`.toLowerCase();
  return `<div class="debug-browser-item" data-debug-browser-item data-debug-kind="entity" data-debug-search="${escapeAttr(search)}" data-test="debug-entity-${escapeAttr(entity.id)}">
    <div><strong>${escapeHtml(entity.name || entity.id)}</strong><span>${escapeHtml(entity.id)} · ${escapeHtml(entity.type || '?')}</span></div>
    <div class="debug-browser-meta">${escapeHtml(entity.location || '未知位置')} · HP ${attrs.hp ?? '?'} / ${attrs.max_hp ?? '?'}${tags ? ` · ${escapeHtml(tags)}` : ''}</div>
  </div>`;
}

function renderDebugFlagRow(key, value) {
  const text = JSON.stringify(value);
  const search = `${key} ${text}`.toLowerCase();
  return `<div class="debug-browser-item" data-debug-browser-item data-debug-kind="flag" data-debug-search="${escapeAttr(search)}" data-test="debug-flag-${escapeAttr(key)}">
    <div><strong>${escapeHtml(key)}</strong><span>${debugFlagSummary(value)}</span></div>
    <pre>${escapeHtml(text.length > 220 ? `${text.slice(0, 220)}…` : text)}</pre>
  </div>`;
}

function debugFlagSummary(value) {
  if (Array.isArray(value)) return `${value.length} 项`;
  if (value && typeof value === "object") return `${Object.keys(value).length} 键`;
  return escapeHtml(String(value));
}

function bindDebugConsoleEvents() {
  const body = $("#debug-body");
  const input = body.querySelector('[data-test="debug-browser-filter"]');
  if (input) {
    input.addEventListener("input", () => applyDebugBrowserFilter(body, input.value));
  }
  const exportBtn = body.querySelector('[data-test="debug-export-bundle"]');
  if (exportBtn) {
    exportBtn.addEventListener("click", exportDebugBundle);
  }
  const createBtn = body.querySelector('[data-test="debug-snapshot-create"]');
  if (createBtn) {
    createBtn.addEventListener("click", createDebugTestSnapshot);
  }
  const exportIndexBtn = body.querySelector('[data-test="debug-snapshot-index-export"]');
  if (exportIndexBtn) {
    exportIndexBtn.addEventListener("click", () => exportDebugTestSnapshotIndex(exportIndexBtn));
  }
  const healthCheckBtn = body.querySelector('[data-test="debug-snapshot-health-check"]');
  if (healthCheckBtn) {
    healthCheckBtn.addEventListener("click", () => checkDebugTestSnapshotHealth(healthCheckBtn));
  }
  const healthExportBtn = body.querySelector('[data-test="debug-snapshot-health-export"]');
  if (healthExportBtn) {
    healthExportBtn.addEventListener("click", () => exportDebugTestSnapshotHealth(healthExportBtn));
  }
  body.querySelectorAll("[data-debug-health-focus]").forEach((btn) => {
    btn.addEventListener("click", () => focusDebugHealthSnapshot(btn.dataset.debugHealthFocus));
  });
  const importBtn = body.querySelector('[data-test="debug-snapshot-import-file"]');
  const importInput = body.querySelector('[data-test="debug-snapshot-file-input"]');
  if (importBtn && importInput) {
    importBtn.addEventListener("click", () => importInput.click());
    importInput.addEventListener("change", importDebugTestSnapshotFile);
  }
  const bundleImportBtn = body.querySelector('[data-test="debug-snapshot-bundle-import-file"]');
  const bundleImportInput = body.querySelector('[data-test="debug-snapshot-bundle-file-input"]');
  if (bundleImportBtn && bundleImportInput) {
    bundleImportBtn.addEventListener("click", () => bundleImportInput.click());
    bundleImportInput.addEventListener("change", importDebugTestSnapshotBundleFile);
  }
  body.querySelectorAll("[data-debug-snapshot-quick-filter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const filter = btn.dataset.debugSnapshotQuickFilter;
      debugSnapshotTagFilter = "";
      if (filter === "all") {
        debugSnapshotQuery = "";
        debugSnapshotShowArchived = true;
      } else if (filter === "pinned") {
        debugSnapshotQuery = "pinned";
        debugSnapshotShowArchived = true;
      } else if (filter === "archived") {
        debugSnapshotQuery = "archived";
        debugSnapshotShowArchived = true;
      } else {
        debugSnapshotQuery = "";
        debugSnapshotShowArchived = false;
      }
      body.innerHTML = renderDebugConsole(window.__lastDebugConsoleData || {});
      bindDebugConsoleEvents();
    });
  });
  body.querySelectorAll("[data-debug-snapshot-quick-tag]").forEach((btn) => {
    btn.addEventListener("click", () => {
      debugSnapshotQuery = "";
      debugSnapshotTagFilter = btn.dataset.debugSnapshotQuickTag;
      debugSnapshotShowArchived = true;
      body.innerHTML = renderDebugConsole(window.__lastDebugConsoleData || {});
      bindDebugConsoleEvents();
    });
  });
  const snapshotFilter = body.querySelector('[data-test="debug-snapshot-filter"]');
  if (snapshotFilter) {
    snapshotFilter.addEventListener("input", () => {
      debugSnapshotQuery = snapshotFilter.value;
      body.innerHTML = renderDebugConsole(window.__lastDebugConsoleData || {});
      bindDebugConsoleEvents();
      body.querySelector('[data-test="debug-snapshot-filter"]')?.focus();
    });
  }
  const snapshotTagFilter = body.querySelector('[data-test="debug-snapshot-tag-filter"]');
  if (snapshotTagFilter) {
    snapshotTagFilter.addEventListener("change", () => {
      debugSnapshotTagFilter = snapshotTagFilter.value;
      body.innerHTML = renderDebugConsole(window.__lastDebugConsoleData || {});
      bindDebugConsoleEvents();
    });
  }
  const snapshotSort = body.querySelector('[data-test="debug-snapshot-sort"]');
  if (snapshotSort) {
    snapshotSort.addEventListener("change", () => {
      debugSnapshotSort = snapshotSort.value;
      body.innerHTML = renderDebugConsole(window.__lastDebugConsoleData || {});
      bindDebugConsoleEvents();
    });
  }
  const snapshotShowArchived = body.querySelector('[data-test="debug-snapshot-show-archived"]');
  if (snapshotShowArchived) {
    snapshotShowArchived.addEventListener("change", () => {
      debugSnapshotShowArchived = snapshotShowArchived.checked;
      body.innerHTML = renderDebugConsole(window.__lastDebugConsoleData || {});
      bindDebugConsoleEvents();
    });
  }
  const clearSnapshotFilter = body.querySelector('[data-test="debug-snapshot-filter-clear"]');
  if (clearSnapshotFilter) {
    clearSnapshotFilter.addEventListener("click", () => {
      debugSnapshotQuery = "";
      debugSnapshotTagFilter = "";
      body.innerHTML = renderDebugConsole(window.__lastDebugConsoleData || {});
      bindDebugConsoleEvents();
    });
  }
  body.querySelectorAll("[data-debug-snapshot-select]").forEach((input) => {
    input.addEventListener("change", () => {
      if (input.checked) debugSnapshotSelectedIds.add(input.dataset.debugSnapshotSelect);
      else debugSnapshotSelectedIds.delete(input.dataset.debugSnapshotSelect);
      body.innerHTML = renderDebugConsole(window.__lastDebugConsoleData || {});
      bindDebugConsoleEvents();
    });
  });
  const selectVisible = body.querySelector('[data-test="debug-snapshot-select-visible"]');
  if (selectVisible) {
    selectVisible.addEventListener("change", () => {
      const query = debugSnapshotQuery.trim().toLowerCase();
      const tagFilter = debugSnapshotTagFilter.trim();
      const visibleIds = sortDebugSnapshots(debugTestSnapshots.filter((snapshot) => {
        const matchesArchived = debugSnapshotShowArchived || !snapshot.archived;
        const matchesQuery = !query || debugSnapshotSearchText(snapshot).includes(query);
        const matchesTag = !tagFilter || (snapshot.tags || []).includes(tagFilter);
        return matchesArchived && matchesQuery && matchesTag;
      })).map((snapshot) => snapshot.id).filter(Boolean);
      visibleIds.forEach((id) => selectVisible.checked ? debugSnapshotSelectedIds.add(id) : debugSnapshotSelectedIds.delete(id));
      body.innerHTML = renderDebugConsole(window.__lastDebugConsoleData || {});
      bindDebugConsoleEvents();
    });
  }
  const clearSelection = body.querySelector('[data-test="debug-snapshot-selection-clear"]');
  if (clearSelection) {
    clearSelection.addEventListener("click", () => {
      debugSnapshotSelectedIds.clear();
      body.innerHTML = renderDebugConsole(window.__lastDebugConsoleData || {});
      bindDebugConsoleEvents();
    });
  }
  const bulkExport = body.querySelector('[data-test="debug-snapshot-bulk-export"]');
  if (bulkExport) {
    bulkExport.addEventListener("click", () => bulkExportDebugTestSnapshots(bulkExport));
  }
  const bulkArchive = body.querySelector('[data-test="debug-snapshot-bulk-archive"]');
  if (bulkArchive) {
    bulkArchive.addEventListener("click", () => bulkArchiveDebugTestSnapshots(true, bulkArchive));
  }
  const bulkUnarchive = body.querySelector('[data-test="debug-snapshot-bulk-unarchive"]');
  if (bulkUnarchive) {
    bulkUnarchive.addEventListener("click", () => bulkArchiveDebugTestSnapshots(false, bulkUnarchive));
  }
  const bulkDelete = body.querySelector('[data-test="debug-snapshot-bulk-delete"]');
  if (bulkDelete) {
    bulkDelete.addEventListener("click", () => bulkDeleteDebugTestSnapshots(bulkDelete));
  }
  const confirmBundleImport = body.querySelector('[data-test="debug-snapshot-bundle-confirm-import"]');
  if (confirmBundleImport) {
    confirmBundleImport.addEventListener("click", () => confirmDebugTestSnapshotBundleImport(confirmBundleImport));
  }
  const cancelBundleImport = body.querySelector('[data-test="debug-snapshot-bundle-cancel-import"]');
  if (cancelBundleImport) {
    cancelBundleImport.addEventListener("click", () => {
      debugSnapshotBundleImportPreview = null;
      body.innerHTML = renderDebugConsole(window.__lastDebugConsoleData || {});
      bindDebugConsoleEvents();
    });
  }
  body.querySelectorAll("[data-debug-snapshot-load]").forEach((btn) => {
    btn.addEventListener("click", () => prepareDebugTestSnapshotLoad(btn.dataset.debugSnapshotLoad, btn));
  });
  body.querySelectorAll("[data-debug-snapshot-confirm-load]").forEach((btn) => {
    btn.addEventListener("click", () => loadDebugTestSnapshot(btn.dataset.debugSnapshotConfirmLoad, btn));
  });
  body.querySelectorAll("[data-debug-snapshot-cancel-load]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      delete debugSnapshotLoadConfirmations[btn.dataset.debugSnapshotCancelLoad];
      await refreshDebugConsole();
    });
  });
  body.querySelectorAll("[data-debug-snapshot-detail]").forEach((btn) => {
    btn.addEventListener("click", () => loadDebugSnapshotDetail(btn.dataset.debugSnapshotDetail, btn));
  });
  body.querySelectorAll("[data-debug-snapshot-diff]").forEach((btn) => {
    btn.addEventListener("click", () => loadDebugSnapshotDiff(btn.dataset.debugSnapshotDiff, btn));
  });
  body.querySelectorAll("[data-debug-snapshot-export]").forEach((btn) => {
    btn.addEventListener("click", () => exportDebugTestSnapshot(btn.dataset.debugSnapshotExport, btn.dataset.debugSnapshotName || btn.dataset.debugSnapshotExport, btn));
  });
  body.querySelectorAll("[data-debug-snapshot-pin]").forEach((btn) => {
    btn.addEventListener("click", () => toggleDebugTestSnapshotPin(btn.dataset.debugSnapshotPin, btn.dataset.debugSnapshotPinned === "true", btn));
  });
  body.querySelectorAll("[data-debug-snapshot-archive]").forEach((btn) => {
    btn.addEventListener("click", () => toggleDebugTestSnapshotArchive(btn.dataset.debugSnapshotArchive, btn.dataset.debugSnapshotArchived === "true", btn));
  });
  body.querySelectorAll("[data-debug-snapshot-duplicate]").forEach((btn) => {
    btn.addEventListener("click", () => duplicateDebugTestSnapshot(btn.dataset.debugSnapshotDuplicate, btn.dataset.debugSnapshotName || btn.dataset.debugSnapshotDuplicate, btn));
  });
  body.querySelectorAll("[data-debug-snapshot-save]").forEach((btn) => {
    btn.addEventListener("click", () => updateDebugTestSnapshot(btn.dataset.debugSnapshotSave, btn));
  });
  body.querySelectorAll("[data-debug-snapshot-delete]").forEach((btn) => {
    btn.addEventListener("click", () => deleteDebugTestSnapshot(btn.dataset.debugSnapshotDelete, btn));
  });
  body.querySelectorAll("[data-debug-preset-load]").forEach((btn) => {
    btn.addEventListener("click", () => loadDebugTestPreset(btn.dataset.debugPresetLoad, btn));
  });
  const toolNameFilter = body.querySelector('[data-test="debug-tool-name-filter"]');
  if (toolNameFilter) {
    toolNameFilter.addEventListener("change", () => {
      debugToolFilter = toolNameFilter.value;
      refreshDebugConsole();
    });
  }
  const toolQueryFilter = body.querySelector('[data-test="debug-tool-query-filter"]');
  if (toolQueryFilter) {
    toolQueryFilter.addEventListener("input", () => {
      debugToolQuery = toolQueryFilter.value;
      refreshDebugConsole();
    });
  }
  const clearToolFilter = body.querySelector('[data-test="debug-tool-filter-clear"]');
  if (clearToolFilter) {
    clearToolFilter.addEventListener("click", () => {
      debugToolFilter = "";
      debugToolQuery = "";
      refreshDebugConsole();
    });
  }
  body.querySelectorAll("[data-debug-copy]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await copyText(btn.dataset.debugCopyText || "");
      btn.textContent = `已复制${btn.dataset.debugCopy || ""}`;
    });
  });
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return;
  } catch (_) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
  }
}

async function refreshDebugConsole() {
  const params = new URLSearchParams({ limit: "20" });
  if (debugToolFilter) params.set("tool", debugToolFilter);
  if (debugToolQuery) params.set("q", debugToolQuery);
  const data = await api(`/api/debug/console?${params.toString()}`);
  const snapshots = await api("/api/debug/test-snapshots");
  const presets = await api("/api/debug/test-presets");
  const snapshotIds = new Set((snapshots.snapshots || []).map((s) => s.id));
  for (const id of Array.from(debugSnapshotSelectedIds)) {
    if (!snapshotIds.has(id)) debugSnapshotSelectedIds.delete(id);
  }
  for (const key of Object.keys(debugSnapshotDiffs)) {
    if (!snapshotIds.has(key)) delete debugSnapshotDiffs[key];
  }
  for (const key of Object.keys(debugSnapshotDetails)) {
    if (!snapshotIds.has(key)) delete debugSnapshotDetails[key];
  }
  for (const key of Object.keys(debugSnapshotLoadConfirmations)) {
    if (!snapshotIds.has(key)) delete debugSnapshotLoadConfirmations[key];
  }
  debugTestSnapshots = snapshots.snapshots || [];
  debugTestSnapshotSummary = snapshots.summary || { snapshot_count: debugTestSnapshots.length, totals: {}, latest_updated_at: "" };
  debugTestPresets = presets.presets || [];
  window.__lastDebugConsoleData = data;
  const body = $("#debug-body");
  body.innerHTML = renderDebugConsole(data);
  bindDebugConsoleEvents();
}

async function exportDebugBundle() {
  const params = new URLSearchParams({ limit: "20" });
  if (debugToolFilter) params.set("tool", debugToolFilter);
  if (debugToolQuery) params.set("q", debugToolQuery);
  const data = await api(`/api/debug/export?${params.toString()}`);
  downloadJson(`mingrpg-debug-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}.json`, data);
  addBubble("system", "已导出调试包。");
}

async function createDebugTestSnapshot() {
  const body = $("#debug-body");
  const nameInput = body.querySelector('[data-test="debug-snapshot-name"]');
  const noteInput = body.querySelector('[data-test="debug-snapshot-note"]');
  const tagsInput = body.querySelector('[data-test="debug-snapshot-tags"]');
  const name = (nameInput?.value || "").trim();
  const note = (noteInput?.value || "").trim();
  const tags = parseDebugSnapshotTags(tagsInput?.value || "");
  if (!name) {
    addBubble("system", "测试快照名称不能为空。");
    nameInput?.focus();
    return;
  }
  await api("/api/debug/test-snapshots", {
    method: "POST",
    body: JSON.stringify({ name, note, tags }),
  });
  await refreshDebugConsole();
  addBubble("system", `已保存测试快照「${name}」。`);
}

async function prepareDebugTestSnapshotLoad(snapshotId, button) {
  if (button) button.disabled = true;
  try {
    const res = await api(`/api/debug/test-snapshots/${encodeURIComponent(snapshotId)}`);
    debugSnapshotLoadConfirmations = { [snapshotId]: res.snapshot };
    await refreshDebugConsole();
  } catch (e) {
    addBubble("system", `获取快照加载确认失败: ${e.message}`);
    if (button) button.disabled = false;
  }
}

async function loadDebugTestSnapshot(snapshotId, button) {
  if (button) button.disabled = true;
  try {
    const res = await api("/api/debug/test-snapshots/load", {
      method: "POST",
      body: JSON.stringify({ snapshot_id: snapshotId }),
    });
    chat.innerHTML = "";
    addBubble("system", `已加载测试快照「${res.snapshot.name}」。`);
    showOpeningForState(res.state);
    renderSidePanel(res.state);
    renderScene(res.state);
    debugSnapshotDiffs = {};
    debugSnapshotDetails = {};
    debugSnapshotLoadConfirmations = {};
    await refreshDebugConsole();
  } catch (e) {
    addBubble("system", `加载测试快照失败: ${e.message}`);
    if (button) button.disabled = false;
  }
}

async function loadDebugSnapshotDetail(snapshotId, button) {
  if (button) button.disabled = true;
  try {
    const res = await api(`/api/debug/test-snapshots/${encodeURIComponent(snapshotId)}`);
    debugSnapshotDetails[snapshotId] = debugSnapshotDetails[snapshotId] ? null : res.snapshot;
    await refreshDebugConsole();
  } catch (e) {
    addBubble("system", `获取快照详情失败: ${e.message}`);
  }
  if (button) button.disabled = false;
}

async function loadDebugSnapshotDiff(snapshotId, button) {
  if (button) button.disabled = true;
  try {
    const diff = await api(`/api/debug/test-snapshots/${encodeURIComponent(snapshotId)}/diff`);
    debugSnapshotDiffs[snapshotId] = debugSnapshotDiffs[snapshotId] ? null : diff;
    await refreshDebugConsole();
  } catch (e) {
    addBubble("system", `获取差异失败: ${e.message}`);
  }
  if (button) button.disabled = false;
}

async function exportDebugTestSnapshot(snapshotId, snapshotName, button) {
  if (button) button.disabled = true;
  try {
    const data = await api(`/api/debug/test-snapshots/${encodeURIComponent(snapshotId)}/export`);
    const safeName = String(snapshotName || snapshotId).replace(/[^\w\u4e00-\u9fa5.-]+/g, "-").replace(/^-+|-+$/g, "") || snapshotId;
    downloadJson(`mingrpg-test-snapshot-${safeName}.json`, data);
    await refreshDebugConsole();
    addBubble("system", `已导出测试快照「${snapshotName || snapshotId}」。`);
  } catch (e) {
    addBubble("system", `导出测试快照失败: ${e.message}`);
  }
  if (button) button.disabled = false;
}

async function exportDebugTestSnapshotIndex(button) {
  if (button) button.disabled = true;
  try {
    const data = await api("/api/debug/test-snapshots/export-index");
    downloadJson(`mingrpg-test-snapshot-index-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}.json`, data);
    addBubble("system", `已导出 ${data.snapshot_count ?? 0} 个测试快照索引。`);
  } catch (e) {
    addBubble("system", `导出测试快照索引失败: ${e.message}`);
  }
  if (button) button.disabled = false;
}

async function checkDebugTestSnapshotHealth(button) {
  if (button) button.disabled = true;
  try {
    debugSnapshotHealth = await api("/api/debug/test-snapshots/health");
    await refreshDebugConsole();
    addBubble("system", debugSnapshotHealth.issue_count ? `快照校验发现 ${debugSnapshotHealth.issue_count} 个问题。` : "快照校验通过。");
  } catch (e) {
    addBubble("system", `校验测试快照失败: ${e.message}`);
    if (button) button.disabled = false;
  }
}

async function exportDebugTestSnapshotHealth(button) {
  if (button) button.disabled = true;
  try {
    const data = await api("/api/debug/test-snapshots/health/export");
    debugSnapshotHealth = data;
    downloadJson(`mingrpg-test-snapshot-health-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}.json`, data);
    await refreshDebugConsole();
    addBubble("system", `已导出测试快照校验报告,发现 ${data.issue_count ?? 0} 个问题。`);
  } catch (e) {
    addBubble("system", `导出测试快照校验报告失败: ${e.message}`);
    if (button) button.disabled = false;
  }
}

function focusDebugHealthSnapshot(snapshotId) {
  if (!snapshotId) return;
  debugSnapshotQuery = snapshotId;
  debugSnapshotShowArchived = true;
  const body = $("#debug-body");
  body.innerHTML = renderDebugConsole(window.__lastDebugConsoleData || {});
  bindDebugConsoleEvents();
  const item = body.querySelector(`[data-test="debug-snapshot-${CSS.escape(snapshotId)}"]`);
  const input = body.querySelector('[data-test="debug-snapshot-filter"]');
  if (input) input.value = snapshotId;
  if (!item) return;
  item.classList.add("focused");
  item.scrollIntoView({ behavior: "smooth", block: "center" });
  setTimeout(() => item.classList.remove("focused"), 1600);
}

async function toggleDebugTestSnapshotPin(snapshotId, pinned, button) {
  if (button) button.disabled = true;
  try {
    const res = await api(`/api/debug/test-snapshots/${encodeURIComponent(snapshotId)}`, {
      method: "PATCH",
      body: JSON.stringify({ pinned: !pinned }),
    });
    await refreshDebugConsole();
    addBubble("system", `${res.snapshot.pinned ? '已置顶' : '已取消置顶'}测试快照「${res.snapshot.name}」。`);
  } catch (e) {
    addBubble("system", `更新测试快照置顶失败: ${e.message}`);
    if (button) button.disabled = false;
  }
}

async function toggleDebugTestSnapshotArchive(snapshotId, archived, button) {
  if (button) button.disabled = true;
  try {
    const res = await api(`/api/debug/test-snapshots/${encodeURIComponent(snapshotId)}`, {
      method: "PATCH",
      body: JSON.stringify({ archived: !archived }),
    });
    debugSnapshotSelectedIds.delete(snapshotId);
    await refreshDebugConsole();
    addBubble("system", `${res.snapshot.archived ? '已归档' : '已取消归档'}测试快照「${res.snapshot.name}」。`);
  } catch (e) {
    addBubble("system", `更新测试快照归档失败: ${e.message}`);
    if (button) button.disabled = false;
  }
}

async function duplicateDebugTestSnapshot(snapshotId, snapshotName, button) {
  if (button) button.disabled = true;
  try {
    const res = await api(`/api/debug/test-snapshots/${encodeURIComponent(snapshotId)}/duplicate`, {
      method: "POST",
      body: JSON.stringify({ name: `${snapshotName || snapshotId} 副本` }),
    });
    await refreshDebugConsole();
    addBubble("system", `已复制测试快照「${res.snapshot.name}」。`);
  } catch (e) {
    addBubble("system", `复制测试快照失败: ${e.message}`);
    if (button) button.disabled = false;
  }
}

async function importDebugTestSnapshotFile(ev) {
  const file = ev.target.files && ev.target.files[0];
  ev.target.value = "";
  if (!file) return;
  try {
    const snapshot = JSON.parse(await file.text());
    const res = await api("/api/debug/test-snapshots/import", {
      method: "POST",
      body: JSON.stringify({ snapshot }),
    });
    chat.innerHTML = "";
    addBubble("system", `已导入测试快照「${res.snapshot.name || res.snapshot.id}」。`);
    showOpeningForState(res.state);
    renderSidePanel(res.state);
    renderScene(res.state);
    debugSnapshotDiffs = {};
    debugSnapshotDetails = {};
    debugSnapshotLoadConfirmations = {};
    await refreshDebugConsole();
  } catch (e) {
    addBubble("system", `导入测试快照失败: ${e.message}`);
  }
}

async function importDebugTestSnapshotBundleFile(ev) {
  const file = ev.target.files && ev.target.files[0];
  ev.target.value = "";
  if (!file) return;
  try {
    const bundle = JSON.parse(await file.text());
    const preview = await api("/api/debug/test-snapshots/bulk-import/preview", {
      method: "POST",
      body: JSON.stringify({ bundle }),
    });
    debugSnapshotBundleImportPreview = { ...preview, bundle, file_name: file.name };
    await refreshDebugConsole();
    addBubble("system", `已预览 ${preview.snapshot_count} 个测试快照,确认后导入。`);
  } catch (e) {
    addBubble("system", `预览测试快照包失败: ${e.message}`);
  }
}

async function confirmDebugTestSnapshotBundleImport(button) {
  if (!debugSnapshotBundleImportPreview?.bundle) return;
  if (button) button.disabled = true;
  try {
    const res = await api("/api/debug/test-snapshots/bulk-import", {
      method: "POST",
      body: JSON.stringify({ bundle: debugSnapshotBundleImportPreview.bundle }),
    });
    debugSnapshotDiffs = {};
    debugSnapshotDetails = {};
    debugSnapshotLoadConfirmations = {};
    debugSnapshotBundleImportPreview = null;
    debugSnapshotSelectedIds.clear();
    await refreshDebugConsole();
    addBubble("system", `已导入 ${res.imported.length} 个测试快照。`);
  } catch (e) {
    addBubble("system", `导入测试快照包失败: ${e.message}`);
    if (button) button.disabled = false;
  }
}

async function updateDebugTestSnapshot(snapshotId, button) {
  const editor = button?.closest("[data-debug-snapshot-edit]");
  const inputs = editor ? editor.querySelectorAll("input") : [];
  const name = (inputs[0]?.value || "").trim();
  const note = (inputs[1]?.value || "").trim();
  const tags = parseDebugSnapshotTags(inputs[2]?.value || "");
  if (!name) {
    addBubble("system", "测试快照名称不能为空。");
    inputs[0]?.focus();
    return;
  }
  if (button) button.disabled = true;
  try {
    const res = await api(`/api/debug/test-snapshots/${encodeURIComponent(snapshotId)}`, {
      method: "PATCH",
      body: JSON.stringify({ name, note, tags }),
    });
    debugSnapshotDiffs[snapshotId] = null;
    debugSnapshotDetails[snapshotId] = null;
    debugSnapshotLoadConfirmations[snapshotId] = null;
    await refreshDebugConsole();
    addBubble("system", `已更新测试快照「${res.snapshot.name}」。`);
  } catch (e) {
    addBubble("system", `更新测试快照失败: ${e.message}`);
    if (button) button.disabled = false;
  }
}

async function deleteDebugTestSnapshot(snapshotId, button) {
  if (!confirm("确定删除这个测试快照?此操作不可撤销。")) return;
  if (button) button.disabled = true;
  try {
    const res = await api(`/api/debug/test-snapshots/${encodeURIComponent(snapshotId)}`, {
      method: "DELETE",
    });
    debugSnapshotSelectedIds.delete(snapshotId);
    delete debugSnapshotDiffs[snapshotId];
    delete debugSnapshotDetails[snapshotId];
    delete debugSnapshotLoadConfirmations[snapshotId];
    await refreshDebugConsole();
    addBubble("system", `已删除测试快照「${res.snapshot.name || snapshotId}」。`);
  } catch (e) {
    addBubble("system", `删除测试快照失败: ${e.message}`);
    if (button) button.disabled = false;
  }
}

async function bulkExportDebugTestSnapshots(button) {
  const snapshotIds = Array.from(debugSnapshotSelectedIds);
  if (!snapshotIds.length) return;
  if (button) button.disabled = true;
  try {
    const data = await api("/api/debug/test-snapshots/bulk-export", {
      method: "POST",
      body: JSON.stringify({ snapshot_ids: snapshotIds }),
    });
    downloadJson(`mingrpg-test-snapshot-bundle-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}.json`, data);
    addBubble("system", `已导出 ${data.snapshot_count ?? snapshotIds.length} 个测试快照。`);
  } catch (e) {
    addBubble("system", `批量导出测试快照失败: ${e.message}`);
  }
  if (button) button.disabled = false;
}

async function bulkArchiveDebugTestSnapshots(archived, button) {
  const snapshotIds = Array.from(debugSnapshotSelectedIds);
  if (!snapshotIds.length) return;
  if (button) button.disabled = true;
  try {
    const res = await api("/api/debug/test-snapshots/bulk-archive", {
      method: "POST",
      body: JSON.stringify({ snapshot_ids: snapshotIds, archived }),
    });
    debugSnapshotSelectedIds.clear();
    await refreshDebugConsole();
    addBubble("system", `${archived ? '已归档' : '已取消归档'} ${res.archived.length} 个测试快照。`);
  } catch (e) {
    addBubble("system", `批量${archived ? '归档' : '取消归档'}测试快照失败: ${e.message}`);
    if (button) button.disabled = false;
  }
}

async function bulkDeleteDebugTestSnapshots(button) {
  const snapshotIds = Array.from(debugSnapshotSelectedIds);
  if (!snapshotIds.length) return;
  if (!confirm(`确定删除所选 ${snapshotIds.length} 个测试快照?此操作不可撤销。`)) return;
  if (button) button.disabled = true;
  try {
    const res = await api("/api/debug/test-snapshots/bulk-delete", {
      method: "POST",
      body: JSON.stringify({ snapshot_ids: snapshotIds }),
    });
    for (const snapshotId of snapshotIds) {
      delete debugSnapshotDiffs[snapshotId];
      delete debugSnapshotDetails[snapshotId];
      delete debugSnapshotLoadConfirmations[snapshotId];
    }
    debugSnapshotSelectedIds.clear();
    await refreshDebugConsole();
    addBubble("system", `已删除 ${res.deleted.length} 个测试快照。`);
  } catch (e) {
    addBubble("system", `批量删除测试快照失败: ${e.message}`);
    if (button) button.disabled = false;
  }
}

async function loadDebugTestPreset(presetId, button) {
  if (button) button.disabled = true;
  try {
    const res = await api("/api/debug/test-presets/load", {
      method: "POST",
      body: JSON.stringify({ preset_id: presetId }),
    });
    chat.innerHTML = "";
    addBubble("system", `已加载预设测试用例「${res.preset.name}」。`);
    showOpeningForState(res.state);
    renderSidePanel(res.state);
    renderScene(res.state);
    await refreshDebugConsole();
  } catch (e) {
    addBubble("system", `加载预设测试用例失败: ${e.message}`);
    if (button) button.disabled = false;
  }
}

function applyDebugBrowserFilter(body, rawQuery) {
  const query = (rawQuery || "").trim().toLowerCase();
  let entityCount = 0;
  let flagCount = 0;
  body.querySelectorAll("[data-debug-browser-item]").forEach((item) => {
    const matched = !query || (item.dataset.debugSearch || "").includes(query);
    item.classList.toggle("debug-hidden", !matched);
    if (matched && item.dataset.debugKind === "entity") entityCount += 1;
    if (matched && item.dataset.debugKind === "flag") flagCount += 1;
  });
  const entityCountEl = body.querySelector('[data-test="debug-entity-count"]');
  const flagCountEl = body.querySelector('[data-test="debug-flag-count"]');
  const empty = body.querySelector('[data-test="debug-browser-empty"]');
  if (entityCountEl) entityCountEl.textContent = String(entityCount);
  if (flagCountEl) flagCountEl.textContent = String(flagCount);
  if (empty) empty.classList.toggle("hidden", !query || entityCount + flagCount > 0);
}

function renderEmptyGuide(icon, title, tips) {
  const tipsHtml = tips.map((t) =>
    `<li>${t.action ? `<button onclick="handleTurn('${escapeAttr(t.action)}')">${escapeHtml(t.label)}</button>` : escapeHtml(t.label)}${t.hint ? `<span>${escapeHtml(t.hint)}</span>` : ''}</li>`
  ).join("");
  return `<div class="empty-guide" data-test="empty-guide">
    <div class="empty-guide-icon">${icon}</div>
    <div class="empty-guide-title">${escapeHtml(title)}</div>
    <ul class="empty-guide-tips">${tipsHtml}</ul>
  </div>`;
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function escapeAttr(s) {
  return escapeHtml(s).replace(/"/g, "&quot;");
}

function formatTimestamp(ts) {
  if (!ts) return "";
  // If already a relative string like "第3回合" or "卯时", return as-is
  if (/回合|时|刻/.test(ts)) return ts;
  // Try parsing as ISO date
  try {
    const d = new Date(ts);
    if (isNaN(d.getTime())) return ts;
    return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`;
  } catch {
    return ts;
  }
}

function showOpening() {
  showOpeningForState(lastSidePanelState);
}

function showOpeningForState(state) {
  const player = state ? (state.entities || []).find((e) => e.id === "player") : null;
  const location = player && state ? (state.locations || []).find((l) => l.id === player.location) : null;
  const identity = ((player || {}).attributes || {}).social_identity || (player || {}).name || "无名书生";
  const place = location ? location.name : "扬州府衙大堂";
  addBubble(
    "gm",
    `你以「${identity}」的身份站在${place}。\n` +
    "万历十年的扬州城人声鼎沸,王知府案牍下的状纸、钱粮、传闻与人情都在暗处流转。\n" +
    "你打算如何应对?",
    "开场"
  );
}

// ===================================================================
// Init
// ===================================================================
showOpening();
initDensityToggle();
initMobilePanelToggle();
initPanelToggles();
initPanelBulkControls();
initSideNav();
initPanelSearch();
initPixi();
connectWS();

// Load initial state and render
(async () => {
  try {
    const state = await api("/api/state");
    renderSidePanel(state);
    // Wait a tick for Pixi to init, then render
    const waitForReady = () => {
      if (window.__rendererReady) {
        renderScene(state);
      } else {
        setTimeout(waitForReady, 100);
      }
    };
    waitForReady();
  } catch (e) {
    setStatus("加载状态失败: " + e.message);
  }
})();

form.addEventListener("submit", (ev) => {
  ev.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;
  inputEl.value = "";
  handleTurn(text);
});

$("#btn-export-save").addEventListener("click", async () => {
  try {
    const save = await api("/api/save");
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    downloadJson(`mingrpg-save-${stamp}.json`, save);
    addBubble("system", "存档已导出为 JSON 文件。可分享给他人导入继续游玩。");
  } catch (e) {
    addBubble("system", `导出失败: ${e.message}`);
  }
});

$("#btn-import-save").addEventListener("click", () => {
  $("#save-file-input").click();
});

$("#btn-birth-settings").addEventListener("click", openBirthModal);
$("#close-birth").addEventListener("click", () => {
  $("#birth-modal").classList.add("hidden");
});

$("#btn-debug-console").addEventListener("click", async () => {
  const modal = $("#debug-modal");
  const body = $("#debug-body");
  body.innerHTML = "<em>加载中...</em>";
  modal.classList.remove("hidden");
  try {
    await refreshDebugConsole();
  } catch (e) {
    body.innerHTML = `<em>加载失败: ${escapeHtml(e.message)}</em>`;
  }
});
$("#close-debug").addEventListener("click", () => {
  $("#debug-modal").classList.add("hidden");
});

$("#save-file-input").addEventListener("change", async (ev) => {
  const file = ev.target.files && ev.target.files[0];
  ev.target.value = "";
  if (!file) return;
  try {
    const save = JSON.parse(await file.text());
    const res = await api("/api/save/import", {
      method: "POST",
      body: JSON.stringify({ save }),
    });
    chat.innerHTML = "";
    addBubble("system", "存档已导入。世界状态已恢复。");
    renderSidePanel(res.state);
    renderScene(res.state);
  } catch (e) {
    addBubble("system", `导入失败: ${e.message}`);
  }
});

$("#btn-reset").addEventListener("click", async () => {
  if (!confirm("确定重置整个世界?所有进度将丢失。")) return;
  await api("/api/reset", { method: "POST" });
  chat.innerHTML = "";
  addBubble("system", "世界已重置。新的开始。");
  showOpening();
  const state = await api("/api/state");
  renderSidePanel(state);
  renderScene(state);
});

$("#btn-audit").addEventListener("click", async () => {
  const modal = $("#audit-modal");
  const body = $("#audit-body");
  body.innerHTML = "<em>加载中...</em>";
  modal.classList.remove("hidden");
  try {
    const data = await api("/api/audit?limit=20");
    body.innerHTML = renderAudit(data.turns);
  } catch (e) {
    body.innerHTML = `<em>加载失败: ${e.message}</em>`;
  }
});

$("#close-audit").addEventListener("click", () => {
  $("#audit-modal").classList.add("hidden");
});

// Review modal: event delegation for .review-open-btn (may exist before listeners)
document.addEventListener("click", async (ev) => {
  const copyBtn = ev.target.closest('[data-test="copy-review"]');
  if (copyBtn) {
    await copyText(copyBtn.dataset.reviewText || "");
    copyBtn.textContent = "已复制";
    return;
  }

  const downloadBtn = ev.target.closest('[data-test="download-review"]');
  if (downloadBtn) {
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    downloadText(`mingrpg-review-${stamp}.txt`, downloadBtn.dataset.reviewText || "");
    return;
  }

  const clearReviewBtn = ev.target.closest('[data-test="review-filter-clear"]');
  if (clearReviewBtn) {
    clearReviewFilter($("#review-body"));
    return;
  }

  const jumpLatestBtn = ev.target.closest('[data-test="review-jump-latest"]');
  if (jumpLatestBtn) {
    const body = $("#review-body");
    const chapters = body.querySelectorAll("[data-review-chapter]");
    const latest = chapters[chapters.length - 1];
    if (latest) latest.scrollIntoView({ behavior: "smooth", block: "start" });
    return;
  }

  const matchNavBtn = ev.target.closest('[data-review-match-nav]');
  if (matchNavBtn) {
    jumpReviewMatch($("#review-body"), matchNavBtn.dataset.reviewMatchNav);
    return;
  }

  const replayBtn = ev.target.closest('[data-test="open-replay"]');
  if (replayBtn) {
    loadReplayPlayer();
    return;
  }

  const btn = ev.target.closest('[data-test="open-review"]');
  if (!btn) return;
  const modal = $("#review-modal");
  const body = $("#review-body");
  body.innerHTML = "<em>加载中...</em>";
  modal.classList.remove("hidden");
  try {
    const data = await api("/api/audit?limit=50");
    body.innerHTML = renderReviewDetail(data.turns, data.total, data.has_more);
    bindReviewEvents(body);
  } catch (e) {
    body.innerHTML = `<em>加载失败: ${e.message}</em>`;
  }
});

$("#close-review").addEventListener("click", () => {
  $("#review-modal").classList.add("hidden");
});

$("#close-replay").addEventListener("click", () => {
  $("#replay-modal").classList.add("hidden");
  stopReplayAutoPlay();
  if (replayKeyHandler) {
    document.removeEventListener("keydown", replayKeyHandler);
    replayKeyHandler = null;
  }
  replayData = null;
});

inputEl.focus();
