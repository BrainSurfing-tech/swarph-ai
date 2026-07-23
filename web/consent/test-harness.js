/*!
 * swarph consent — manual test harness support script (NOT part of the
 * shipped component; only loaded by test.html). External file, no inline
 * script, consistent with the strict-CSP posture of the component itself.
 */
(function () {
  "use strict";
  var logEl = document.getElementById("log");
  var lines = [];

  function render() {
    logEl.textContent = lines.length ? lines.join("\n") : "(waiting for pushes…)";
  }

  function toDisplayArray(entry) {
    // gtag()'s own snippet does dataLayer.push(arguments) -- an
    // arguments object, not a real Array -- so JSON.stringify would
    // otherwise render it as {"0":...,"1":...,"length":n}. Normalize for
    // a readable log; this is purely cosmetic, not a behavior change.
    if (entry && typeof entry.length === "number" && !Array.isArray(entry)) {
      return Array.prototype.slice.call(entry);
    }
    return entry;
  }

  function logPush(entry) {
    lines.push(JSON.stringify(toDisplayArray(entry)));
    render();
  }

  window.dataLayer = window.dataLayer || [];
  // Log anything pushed before this harness attached (the default + any
  // synchronously-replayed stored consent).
  window.dataLayer.forEach(logPush);
  // Wrap push so every future call (Accept/Reject/Save) is logged live too.
  var originalPush = window.dataLayer.push.bind(window.dataLayer);
  window.dataLayer.push = function () {
    var args = Array.prototype.slice.call(arguments);
    args.forEach(logPush);
    return originalPush.apply(null, args);
  };

  var resetBtn = document.getElementById("reset-btn");
  resetBtn.addEventListener("click", function () {
    try { window.localStorage.removeItem("swarph_consent_v1"); } catch (e) { /* ignore */ }
    window.location.reload();
  });
})();
