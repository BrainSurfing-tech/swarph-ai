#!/usr/bin/env node
/*!
 * swarph — headless self-check for the Consent Mode v2 component (card #91)
 *
 * There is no test harness / build tooling in this repo (static, no-build
 * site) and no browser test runner installed, so this exercises the ACTUAL
 * shipped consent-default.js and consent-banner.js source (read from disk,
 * evaluated with Node's built-in `vm` module against a tiny hand-rolled DOM
 * stub) rather than re-implementing their logic. Zero new dependencies.
 *
 * Run:  node web/consent/selfcheck.js
 * Exits non-zero on any failed assertion.
 *
 * A manual, real-browser check is documented in README.md / test.html for
 * anyone who wants to eyeball the actual rendered banner, keyboard nav, etc.
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const assert = require("assert");

const DEFAULT_SRC = fs.readFileSync(path.join(__dirname, "consent-default.js"), "utf8");
const BANNER_SRC = fs.readFileSync(path.join(__dirname, "consent-banner.js"), "utf8");

const DENIED4 = {
  ad_storage: "denied",
  analytics_storage: "denied",
  ad_user_data: "denied",
  ad_personalization: "denied"
};
const GRANTED4 = {
  ad_storage: "granted",
  analytics_storage: "granted",
  ad_user_data: "granted",
  ad_personalization: "granted"
};

// --- minimal fake DOM -------------------------------------------------

function makeElement(tag) {
  const el = {
    tagName: String(tag).toUpperCase(),
    attributes: {},
    children: [],
    parentNode: null,
    _listeners: {},
    _classes: new Set(),
    textContent: "",
    checked: false,
    dataset: {}
  };
  el.classList = {
    add: (...c) => c.forEach((x) => el._classes.add(x)),
    remove: (...c) => c.forEach((x) => el._classes.delete(x)),
    contains: (c) => el._classes.has(c)
  };
  Object.defineProperty(el, "className", {
    get() { return Array.from(el._classes).join(" "); },
    set(v) { el._classes = new Set(String(v).split(/\s+/).filter(Boolean)); }
  });
  Object.defineProperty(el, "firstChild", {
    get() { return el.children[0] || null; }
  });
  el.setAttribute = (name, val) => {
    el.attributes[name] = String(val);
    if (name === "id") el.id = String(val);
  };
  el.getAttribute = (name) =>
    Object.prototype.hasOwnProperty.call(el.attributes, name) ? el.attributes[name] : null;
  el.appendChild = (child) => { child.parentNode = el; el.children.push(child); return child; };
  el.insertBefore = (child, ref) => {
    child.parentNode = el;
    if (ref == null) { el.children.push(child); return child; }
    const idx = el.children.indexOf(ref);
    if (idx === -1) el.children.push(child);
    else el.children.splice(idx, 0, child);
    return child;
  };
  el.remove = () => {
    if (el.parentNode) {
      const i = el.parentNode.children.indexOf(el);
      if (i >= 0) el.parentNode.children.splice(i, 1);
      el.parentNode = null;
    }
  };
  el.addEventListener = (type, fn) => { (el._listeners[type] = el._listeners[type] || []).push(fn); };
  el.dispatchEvent = (type) => { (el._listeners[type] || []).slice().forEach((fn) => fn()); };
  el.querySelector = (sel) => {
    if (sel[0] !== "#") return null;
    const id = sel.slice(1);
    const stack = el.children.slice();
    while (stack.length) {
      const n = stack.shift();
      if (n.id === id) return n;
      if (n.children) stack.push(...n.children);
    }
    return null;
  };
  el.focus = () => {};
  return el;
}

function findById(root, id) {
  if (root.id === id) return root;
  const stack = (root.children || []).slice();
  while (stack.length) {
    const n = stack.shift();
    if (n.id === id) return n;
    if (n.children) stack.push(...n.children);
  }
  return null;
}

function makeLocalStorage() {
  const store = {};
  return {
    getItem: (k) => (Object.prototype.hasOwnProperty.call(store, k) ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
    removeItem: (k) => { delete store[k]; },
    _store: store
  };
}

function makeSandbox() {
  const documentFake = {
    currentScript: null,
    readyState: "loading",
    _listeners: {},
    body: makeElement("body"),
    createElement: (tag) => makeElement(tag),
    createTextNode: (text) => ({ nodeType: 3, textContent: text }),
    getElementById(id) { return findById(this.body, id); },
    addEventListener(type, fn) { (this._listeners[type] = this._listeners[type] || []).push(fn); },
    dispatchEvent(type) { (this._listeners[type] || []).slice().forEach((fn) => fn()); }
  };

  const sandbox = {
    console,
    Date,
    JSON,
    parseInt,
    Object,
    Array,
    String,
    document: documentFake,
    setTimeout: (fn) => fn() // run "async" close animation synchronously for deterministic tests
  };
  sandbox.window = sandbox;
  sandbox.window.localStorage = makeLocalStorage();
  sandbox.window.matchMedia = () => ({ matches: false });
  vm.createContext(sandbox);
  return sandbox;
}

function run(sandbox, src, filename) {
  vm.runInContext(src, sandbox, { filename });
}

function loadDefault(sandbox) {
  run(sandbox, DEFAULT_SRC, "consent-default.js");
}

function loadBanner(sandbox, datasetConfig) {
  sandbox.document.currentScript = { dataset: datasetConfig || {} };
  run(sandbox, BANNER_SRC, "consent-banner.js");
  sandbox.document.currentScript = null;
}

function fireDomReady(sandbox) {
  sandbox.document.readyState = "interactive";
  sandbox.document.dispatchEvent("DOMContentLoaded");
}

// Objects built *inside* the vm sandbox belong to a different realm than
// this host script, so their prototypes differ from host object literals
// even when structurally identical -- assert.deepStrictEqual would fail on
// prototype alone. Round-trip through JSON (host-side) to compare plain
// data, which is all these consent payloads are.
function plain(o) { return JSON.parse(JSON.stringify(o)); }

let failures = 0;
function check(name, fn) {
  try {
    fn();
    console.log("  ok  -", name);
  } catch (e) {
    failures++;
    console.log(" FAIL -", name);
    console.log("       " + (e && e.message ? e.message : e));
  }
}

console.log("swarph consent — headless self-check\n");

// 1. consent-default.js pushes Basic Consent Mode default (denied x4) first.
check("consent-default.js pushes 'consent default' denied-all", () => {
  const sb = makeSandbox();
  loadDefault(sb);
  assert.strictEqual(sb.window.dataLayer.length, 1);
  const [cmd, action, obj] = sb.window.dataLayer[0];
  assert.strictEqual(cmd, "consent");
  assert.strictEqual(action, "default");
  assert.deepStrictEqual(plain(obj), DENIED4);
});

// 2. First-time visitor: no stored consent -> no update pushed yet, banner
//    is NOT built until DOMContentLoaded, and IS built then.
check("first-time visitor: banner builds on DOMContentLoaded, no premature update", () => {
  const sb = makeSandbox();
  loadDefault(sb);
  loadBanner(sb, { privacyUrl: "/privacy", policyVersion: "1", expiryDays: "180" });
  assert.strictEqual(sb.window.dataLayer.length, 1, "no consent update should fire yet");
  assert.strictEqual(sb.document.getElementById("swarph-consent-banner"), null);
  fireDomReady(sb);
  const banner = sb.document.getElementById("swarph-consent-banner");
  assert.ok(banner, "banner should be built after DOMContentLoaded");
  assert.ok(sb.document.getElementById("swc-btn-accept"));
  assert.ok(sb.document.getElementById("swc-btn-reject"));
  assert.ok(sb.document.getElementById("swc-btn-manage"));
});

// 3. Accept All -> consent update granted-all, persisted, banner removed.
check("Accept All grants everything and persists", () => {
  const sb = makeSandbox();
  loadDefault(sb);
  loadBanner(sb, { policyVersion: "1" });
  fireDomReady(sb);
  const accept = sb.document.getElementById("swc-btn-accept");
  accept.dispatchEvent("click");
  const last = sb.window.dataLayer[sb.window.dataLayer.length - 1];
  assert.strictEqual(last[0], "consent");
  assert.strictEqual(last[1], "update");
  assert.deepStrictEqual(plain(last[2]), GRANTED4);
  const stored = JSON.parse(sb.window.localStorage.getItem("swarph_consent_v1"));
  assert.deepStrictEqual(stored.consent, GRANTED4);
  assert.strictEqual(sb.document.getElementById("swarph-consent-banner"), null, "banner removed after choice");
});

// 4. Reject All -> explicit denied-all update, persisted, banner removed.
check("Reject All keeps everything denied and persists explicitly", () => {
  const sb = makeSandbox();
  loadDefault(sb);
  loadBanner(sb, { policyVersion: "1" });
  fireDomReady(sb);
  sb.document.getElementById("swc-btn-reject").dispatchEvent("click");
  const last = sb.window.dataLayer[sb.window.dataLayer.length - 1];
  assert.strictEqual(last[1], "update");
  assert.deepStrictEqual(plain(last[2]), DENIED4);
  const stored = JSON.parse(sb.window.localStorage.getItem("swarph_consent_v1"));
  assert.deepStrictEqual(stored.consent, DENIED4);
});

// 5. Manage preferences: analytics-only grant, ads stay denied.
check("Manage preferences: granular analytics-only grant", () => {
  const sb = makeSandbox();
  loadDefault(sb);
  loadBanner(sb, { policyVersion: "1" });
  fireDomReady(sb);
  const manage = sb.document.getElementById("swc-btn-manage");
  manage.dispatchEvent("click");
  const panel = sb.document.getElementById("swc-panel");
  assert.strictEqual(panel.classList.contains("swc-hidden"), false, "panel should open");
  const analyticsInput = sb.document.getElementById("swc-tg-analytics");
  assert.strictEqual(analyticsInput.checked, false, "toggles must default OFF, never pre-ticked");
  analyticsInput.checked = true; // simulate user turning analytics ON, ads left OFF
  sb.document.getElementById("swc-btn-save").dispatchEvent("click");
  const last = sb.window.dataLayer[sb.window.dataLayer.length - 1];
  assert.strictEqual(last[1], "update");
  assert.deepStrictEqual(plain(last[2]), {
    ad_storage: "denied",
    analytics_storage: "granted",
    ad_user_data: "denied",
    ad_personalization: "denied"
  });
});

// 6. Returning visitor with a valid stored choice: replayed BEFORE
//    DOMContentLoaded (i.e. before GTM would load), banner never shown.
check("returning visitor: stored consent replays before GTM, banner suppressed", () => {
  const sb = makeSandbox();
  sb.window.localStorage.setItem("swarph_consent_v1", JSON.stringify({
    policyVersion: "1",
    timestamp: Date.now(),
    consent: GRANTED4
  }));
  loadDefault(sb);
  loadBanner(sb, { policyVersion: "1" });
  // Must already be applied synchronously, before any DOMContentLoaded / GTM.
  assert.strictEqual(sb.window.dataLayer.length, 2);
  assert.deepStrictEqual(plain(sb.window.dataLayer[1][2]), GRANTED4);
  fireDomReady(sb);
  assert.strictEqual(sb.document.getElementById("swarph-consent-banner"), null, "must not re-show once decided");
});

// 7. Expired stored consent (older than expiryDays) is ignored; re-asks.
check("expired stored consent is ignored and re-asks", () => {
  const sb = makeSandbox();
  const oldTs = Date.now() - 200 * 86400000; // 200 days ago, expiryDays default 180
  sb.window.localStorage.setItem("swarph_consent_v1", JSON.stringify({
    policyVersion: "1",
    timestamp: oldTs,
    consent: GRANTED4
  }));
  loadDefault(sb);
  loadBanner(sb, { policyVersion: "1", expiryDays: "180" });
  assert.strictEqual(sb.window.dataLayer.length, 1, "expired consent must not be replayed");
  fireDomReady(sb);
  assert.ok(sb.document.getElementById("swarph-consent-banner"), "banner should re-appear once expired");
});

// 8. policyVersion bump invalidates old stored consent (forces re-consent).
check("policyVersion bump forces re-consent", () => {
  const sb = makeSandbox();
  sb.window.localStorage.setItem("swarph_consent_v1", JSON.stringify({
    policyVersion: "1",
    timestamp: Date.now(),
    consent: GRANTED4
  }));
  loadDefault(sb);
  loadBanner(sb, { policyVersion: "2" }); // site bumped its policy version
  assert.strictEqual(sb.window.dataLayer.length, 1, "old-version consent must not be replayed");
  fireDomReady(sb);
  assert.ok(sb.document.getElementById("swarph-consent-banner"));
});

// 9. Reopening via window.SwarphConsent.open() (e.g. a footer "Manage
//    cookies" link) after a prior Accept must reflect the CURRENT stored
//    consent in the toggles, not reset them to unchecked.
check("SwarphConsent.open() reopens with toggles reflecting stored consent", () => {
  const sb = makeSandbox();
  loadDefault(sb);
  loadBanner(sb, { policyVersion: "1" });
  fireDomReady(sb);
  sb.document.getElementById("swc-btn-accept").dispatchEvent("click");
  assert.strictEqual(sb.document.getElementById("swarph-consent-banner"), null, "closed after accept");

  sb.window.SwarphConsent.open();
  const analyticsInput = sb.document.getElementById("swc-tg-analytics");
  const adsInput = sb.document.getElementById("swc-tg-ads");
  assert.ok(analyticsInput && adsInput, "reopened banner should exist");
  assert.strictEqual(analyticsInput.checked, true, "should reflect prior Accept All, not reset to unchecked");
  assert.strictEqual(adsInput.checked, true, "should reflect prior Accept All, not reset to unchecked");
});

console.log("");
if (failures) {
  console.log(failures + " check(s) FAILED");
  process.exit(1);
} else {
  console.log("all checks passed");
}
