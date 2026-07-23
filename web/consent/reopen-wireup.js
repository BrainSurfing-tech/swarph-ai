/*
 * reopen-wireup.js — site-authored, CSP-safe (script-src 'self') glue that
 * lets a persistent page control (a footer "Manage cookies" link, a /privacy
 * "Manage Privacy" button) RE-OPEN the consent banner after a prior decision.
 *
 * It attaches click handlers to any of the conventional re-open triggers, so
 * every swarph site can drop this file in without editing consent-banner.js:
 *   - id="manage-privacy"        (privacy-page "Manage Privacy" button)
 *   - id="manage-cookies-link"   (footer "Manage cookies" link)
 *   - any element with [data-swarph-consent-open]  (future-proof, N triggers)
 *
 * Re-opening re-reads the visitor's CURRENT stored choice, satisfying the
 * CNIL "withdraw consent at any time" requirement. Load AFTER consent-banner.js
 * (which defines window.SwarphConsent.open):
 *   <script src="/consent/consent-default.js"></script>
 *   <script src="/consent/consent-banner.js"></script>
 *   <script src="/consent/reopen-wireup.js"></script>
 */
(function (window, document) {
  "use strict";

  function open(ev) {
    if (ev) ev.preventDefault();
    if (window.SwarphConsent && typeof window.SwarphConsent.open === "function") {
      window.SwarphConsent.open();
    }
  }

  function wire() {
    var seen = [];
    ["manage-privacy", "manage-cookies-link"].forEach(function (id) {
      var node = document.getElementById(id);
      if (node) { node.addEventListener("click", open); seen.push(node); }
    });
    var nodes = document.querySelectorAll("[data-swarph-consent-open]");
    for (var i = 0; i < nodes.length; i++) {
      if (seen.indexOf(nodes[i]) === -1) nodes[i].addEventListener("click", open);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wire);
  } else {
    wire();
  }
})(window, document);
