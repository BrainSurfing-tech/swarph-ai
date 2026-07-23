/*!
 * swarph — Consent Mode v2 banner (CNIL/GDPR)
 * Card #91. Owner-spec: gemini (GA4/GTM authority).
 *
 * Vanilla JS, zero dependencies, strict-CSP safe: no inline <script>, no
 * inline event-handler attributes anywhere — every handler is wired with
 * addEventListener from this external file (script-src 'self' compatible).
 *
 * REQUIRED LOAD ORDER in <head>, all as plain blocking <script src>
 * (no defer/async — that keeps execution order == document order, which is
 * what guarantees "before GTM"):
 *   1. consent-default.js   sets Consent Mode default: everything denied
 *   2. consent-banner.js    <- this file: replays any stored choice, then
 *                              (only if there isn't one yet) renders the banner
 *   3. GTM/GA container snippet
 *
 * Configuration is via data-* attributes on THIS script's own <script> tag
 * (kept out of inline JS on purpose):
 *   <script src="/consent/consent-banner.js"
 *           data-privacy-url="/privacy"
 *           data-policy-version="1"
 *           data-expiry-days="180"></script>
 *
 *   data-privacy-url    link shown in the banner copy. Default "/privacy".
 *   data-policy-version bump this to force EVERY visitor to re-consent
 *                        (e.g. after a material change to what you track).
 *                        Default "1".
 *   data-expiry-days    re-ask after this many days even if nothing changed
 *                        (CNIL-recommended consent refresh cadence).
 *                        Default 180.
 */
(function (window, document) {
  "use strict";

  var STORAGE_KEY = "swarph_consent_v1";

  var CATEGORY_KEYS = {
    analytics: ["analytics_storage"],
    ads: ["ad_storage", "ad_user_data", "ad_personalization"]
  };
  var ALL_KEYS = CATEGORY_KEYS.analytics.concat(CATEGORY_KEYS.ads);

  // document.currentScript is only reliable synchronously, during this
  // script's own (non-deferred) execution — capture config right now.
  var scriptEl = document.currentScript;
  var ds = (scriptEl && scriptEl.dataset) || {};
  var config = {
    privacyUrl: ds.privacyUrl || "/privacy",
    policyVersion: ds.policyVersion || "1",
    expiryDays: parseInt(ds.expiryDays, 10) || 180
  };

  // ---------------------------------------------------------------------
  // Consent Mode plumbing
  // ---------------------------------------------------------------------

  function gtagUpdate(consentObj) {
    window.dataLayer = window.dataLayer || [];
    if (typeof window.gtag === "function") {
      window.gtag("consent", "update", consentObj);
    } else {
      // consent-default.js normally defines window.gtag before this file
      // runs; fall back to a raw push so the call is never silently lost.
      window.dataLayer.push(["consent", "update", consentObj]);
    }
  }

  function allGranted() {
    var o = {};
    ALL_KEYS.forEach(function (k) { o[k] = "granted"; });
    return o;
  }
  function allDenied() {
    var o = {};
    ALL_KEYS.forEach(function (k) { o[k] = "denied"; });
    return o;
  }
  function fromCategoryChoice(analyticsGranted, adsGranted) {
    var o = {};
    CATEGORY_KEYS.analytics.forEach(function (k) {
      o[k] = analyticsGranted ? "granted" : "denied";
    });
    CATEGORY_KEYS.ads.forEach(function (k) {
      o[k] = adsGranted ? "granted" : "denied";
    });
    return o;
  }

  function readStored() {
    try {
      var raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      var parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object" || !parsed.consent) return null;
      if (String(parsed.policyVersion) !== String(config.policyVersion)) return null;
      if (!parsed.timestamp) return null;
      var ageDays = (Date.now() - parsed.timestamp) / 86400000;
      if (ageDays > config.expiryDays) return null;
      for (var i = 0; i < ALL_KEYS.length; i++) {
        var v = parsed.consent[ALL_KEYS[i]];
        if (v !== "granted" && v !== "denied") return null;
      }
      return parsed;
    } catch (e) {
      // localStorage unavailable (private browsing quota, etc.) -> treat as
      // "no choice yet"; safe fallback stays denied, banner just re-asks.
      return null;
    }
  }

  function persist(consentObj) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify({
        policyVersion: config.policyVersion,
        timestamp: Date.now(),
        consent: consentObj
      }));
    } catch (e) {
      // Non-fatal: worst case the banner re-appears next visit.
    }
  }

  // Step 1 — replay any valid prior choice synchronously, BEFORE GTM loads.
  var stored = readStored();
  if (stored) {
    gtagUpdate(stored.consent);
  }

  // ---------------------------------------------------------------------
  // Banner UI (only built if there is no valid stored choice, or when
  // reopened explicitly via window.SwarphConsent.open())
  // ---------------------------------------------------------------------

  var reduceMotion = false;
  try {
    reduceMotion = window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch (e) { /* ignore */ }

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    attrs = attrs || {};
    Object.keys(attrs).forEach(function (k) {
      if (k === "class") node.className = attrs[k];
      else if (k === "text") node.textContent = attrs[k];
      else node.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) { node.appendChild(c); });
    return node;
  }

  function buildToggleRow(id, title, desc, checked) {
    var input = el("input", {
      type: "checkbox",
      id: id,
      class: "swc-toggle-input"
    });
    input.checked = !!checked;
    var track = el("span", { class: "swc-toggle-track", "aria-hidden": "true" }, [
      el("span", { class: "swc-toggle-thumb" }, [])
    ]);
    var label = el("label", { for: id, class: "swc-toggle" }, [
      track,
      el("span", { class: "swc-toggle-copy" }, [
        el("span", { class: "swc-toggle-title", text: title }, []),
        el("span", { class: "swc-toggle-desc", text: desc }, [])
      ])
    ]);
    return { row: el("div", { class: "swc-toggle-row" }, [input, label]), input: input };
  }

  function closeBanner(root) {
    if (reduceMotion) {
      root.remove();
      return;
    }
    root.classList.add("swc-closing");
    window.setTimeout(function () {
      if (root.parentNode) root.remove();
    }, 220);
  }

  function buildBanner() {
    var existing = document.getElementById("swarph-consent-banner");
    if (existing) {
      existing.classList.remove("swc-closing");
      existing.querySelector("#swc-panel").classList.add("swc-hidden");
      return existing;
    }

    var msg = el("p", { class: "swc-text" }, []);
    msg.appendChild(document.createTextNode(
      "We use cookies to run analytics and, if you agree, ads personalization. " +
      "Nothing beyond what's strictly necessary is set until you choose. Read our "
    ));
    msg.appendChild(el("a", {
      href: config.privacyUrl,
      class: "swc-link",
      text: "privacy policy"
    }, []));
    msg.appendChild(document.createTextNode("."));

    var btnManage = el("button", {
      type: "button",
      id: "swc-btn-manage",
      class: "swc-btn swc-btn-text",
      "aria-expanded": "false",
      "aria-controls": "swc-panel",
      text: "Manage preferences"
    }, []);
    var btnReject = el("button", {
      type: "button",
      id: "swc-btn-reject",
      class: "swc-btn swc-btn-secondary",
      text: "Reject all"
    }, []);
    var btnAccept = el("button", {
      type: "button",
      id: "swc-btn-accept",
      class: "swc-btn swc-btn-primary",
      text: "Accept all"
    }, []);

    var actions = el("div", { class: "swc-actions" }, [btnManage, btnReject, btnAccept]);

    // Reflect the visitor's CURRENT stored choice if reopening via
    // window.SwarphConsent.open() after a prior decision (e.g. a footer
    // "Manage cookies" link) — re-read fresh rather than relying on the
    // module-level `stored` snapshot, which is only accurate at page load.
    // On a genuine first visit there's nothing stored yet, so both default
    // to unchecked, same as before.
    var current = readStored();
    var analyticsToggle = buildToggleRow(
      "swc-tg-analytics",
      "Analytics",
      "Helps us understand site usage (e.g. Google Analytics). Off by default.",
      current && current.consent.analytics_storage === "granted"
    );
    var adsToggle = buildToggleRow(
      "swc-tg-ads",
      "Advertising & personalization",
      "Ad measurement and personalization signals. Off by default.",
      current && current.consent.ad_storage === "granted"
    );

    var btnBack = el("button", {
      type: "button",
      id: "swc-btn-back",
      class: "swc-btn swc-btn-text",
      text: "Back"
    }, []);
    var btnSave = el("button", {
      type: "button",
      id: "swc-btn-save",
      class: "swc-btn swc-btn-primary",
      text: "Save preferences"
    }, []);

    var panel = el("div", {
      id: "swc-panel",
      class: "swc-panel swc-hidden"
    }, [
      analyticsToggle.row,
      adsToggle.row,
      el("div", { class: "swc-panel-actions" }, [btnBack, btnSave])
    ]);

    var root = el("div", {
      id: "swarph-consent-banner",
      class: "swc-banner",
      role: "region",
      "aria-label": "Cookie consent"
    }, [
      el("div", { class: "swc-inner" }, [msg, actions, panel])
    ]);
    root.setAttribute("aria-live", "polite");

    function decide(consentObj) {
      gtagUpdate(consentObj);
      persist(consentObj);
      closeBanner(root);
    }

    btnAccept.addEventListener("click", function () {
      decide(allGranted());
    });
    btnReject.addEventListener("click", function () {
      decide(allDenied());
    });
    btnManage.addEventListener("click", function () {
      var isOpen = panel.classList.contains("swc-hidden") === false;
      if (isOpen) return;
      panel.classList.remove("swc-hidden");
      btnManage.setAttribute("aria-expanded", "true");
      analyticsToggle.input.focus();
    });
    btnBack.addEventListener("click", function () {
      panel.classList.add("swc-hidden");
      btnManage.setAttribute("aria-expanded", "false");
      btnManage.focus();
    });
    btnSave.addEventListener("click", function () {
      decide(fromCategoryChoice(
        analyticsToggle.input.checked,
        adsToggle.input.checked
      ));
    });

    // Insert first in <body> so keyboard users reach the consent choice
    // before the rest of the page's interactive content. Fixed-position via
    // CSS, so this does not affect visual layout.
    if (document.body.firstChild) {
      document.body.insertBefore(root, document.body.firstChild);
    } else {
      document.body.appendChild(root);
    }
    return root;
  }

  function init() {
    if (stored) return; // a valid choice already exists — never re-show
    buildBanner();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Public, no-inline-JS-required reopen hook so a site can add a persistent
  // footer link ("Manage cookies") without touching this file:
  //   <button id="manage-cookies-link">Manage cookies</button>
  //   <script src="/consent/reopen-wireup.js"></script>  (site-authored,
  //     external, containing:
  //     document.getElementById('manage-cookies-link')
  //       .addEventListener('click', function(){ window.SwarphConsent.open(); });
  window.SwarphConsent = window.SwarphConsent || {};
  window.SwarphConsent.open = function () {
    if (document.body) buildBanner();
  };
})(window, document);
