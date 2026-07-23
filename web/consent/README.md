# Consent Mode v2 banner (card #91)

CNIL/GDPR-compliant consent banner for Google Consent Mode v2. Self-contained,
dependency-free, strict-CSP compatible (`script-src 'self'`). Owner-spec:
gemini (GA4/GTM authority).

## Files

| File | Purpose |
|---|---|
| `consent-default.js` | Basic Consent Mode default: everything denied. Must load first. |
| `consent-banner.js` | Replays a stored choice (before GTM loads) and renders the banner if there isn't one yet. |
| `consent-banner.css` | Banner styles, namespaced under `.swc-` / `#swarph-consent-banner`. |
| `test.html` + `test-harness.js` | Manual, real-browser QA page (not part of the shipped component). |
| `selfcheck.js` | Headless self-check — see "Testing" below. |

## How a site includes it

Add exactly these tags to `<head>`, **in this order**, as plain blocking
`<script src="…">` tags — **no `defer`/`async`** on the two consent scripts,
so they execute in strict document order and are *guaranteed* to run before
the GTM container:

```html
<head>
  <!-- 1. Consent Mode default: everything denied until the visitor chooses -->
  <script src="/consent/consent-default.js"></script>

  <!-- 2. Banner: replays a stored choice, or renders the banner -->
  <script src="/consent/consent-banner.js"
          data-privacy-url="/privacy"
          data-policy-version="1"
          data-expiry-days="180"></script>
  <link rel="stylesheet" href="/consent/consent-banner.css">

  <!-- 3. GTM / GA container snippet goes here, AFTER the two lines above -->
  <script>(function(w,d,s,l,i){...})(window,document,'script','dataLayer','GTM-XXXXXXX');</script>
</head>
```

That's the one-line-per-site integration: copy the two `<script>` tags plus
the `<link>` above `verbatim`, point `data-privacy-url` at the site's actual
privacy/cookie policy page, and leave the existing GTM snippet where it is
(after these three lines, not before).

### Inline alternative for the default snippet (non-strict-CSP sites only)

Sites that allow inline `<script>` may inline step 1 instead of loading
`consent-default.js`, using **exactly** this snippet (also the literal
contents of `consent-default.js`):

```html
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('consent','default',{'ad_storage':'denied','analytics_storage':'denied','ad_user_data':'denied','ad_personalization':'denied'});
</script>
```

`consent-banner.js` itself has **no inline alternative** — it must always be
loaded as an external file, since it wires all its event handlers via
`addEventListener` (no `onclick="…"` attributes anywhere), which is what
makes it safe under `script-src 'self'` with no `'unsafe-inline'`.

## Configuration

All configuration is via `data-*` attributes on the `consent-banner.js`
`<script>` tag itself — deliberately not a global inline config object, to
keep every byte of JS on the page in external, CSP-safe files.

| Attribute | Default | Meaning |
|---|---|---|
| `data-privacy-url` | `/privacy` | Link shown in the banner copy. Point it at the site's real privacy/cookie policy. |
| `data-policy-version` | `1` | Bump this after any material change to what the site tracks — it invalidates every visitor's stored consent and forces a fresh choice. |
| `data-expiry-days` | `180` | Stored consent older than this is treated as expired and re-asked (CNIL-recommended consent refresh cadence). |

## How consent persists and re-applies

- On explicit choice (Accept all / Reject all / Save preferences),
  `consent-banner.js` writes one JSON blob to
  `localStorage['swarph_consent_v1']`:
  `{ policyVersion, timestamp, consent: { ad_storage, analytics_storage, ad_user_data, ad_personalization } }`.
- On every subsequent page load, `consent-banner.js` reads that blob
  **synchronously, at the top of its own execution** — before `DOMContentLoaded`
  and before the GTM script tag that follows it in `<head>` — and, if it's
  present, not expired (`expiryDays`), and matches the current
  `policyVersion`, immediately calls
  `gtag('consent','update', storedConsent)`. This is what guarantees GTM/GA
  tags see the visitor's real consent state from their very first pageview,
  not just from the second one.
- The banner is only built (and only then, once `DOMContentLoaded` fires) if
  no valid stored choice exists. A returning visitor with a valid choice
  never sees the banner again.
- If `localStorage` is unavailable (private-browsing quota, etc.), the
  banner degrades to "ask every visit" — it never silently assumes consent.

## CNIL requirements this implements

- **Reject is as easy as Accept**: `Accept all` and `Reject all` are the
  same size, weight, and shape, in the initial view, one click each — no
  extra scroll or step to refuse (`consent-banner.css`, `.swc-btn-primary` /
  `.swc-btn-secondary`).
- **No pre-ticked boxes**: both toggles in "Manage preferences" default to
  unchecked/denied every time the panel is opened.
- **No implied consent from inaction**: there is deliberately no "X" /
  dismiss control on the banner. A visitor must click Accept, Reject, or
  Save preferences — continuing to browse without choosing leaves Consent
  Mode at its default-denied state indefinitely (banner just re-appears).
- **Granular choice**: "Manage preferences" exposes Analytics
  (`analytics_storage`) and Advertising & personalization (`ad_storage` +
  `ad_user_data` + `ad_personalization` grouped) as independent toggles —
  the grouping of the three `ad_*` signals is the one deliberate v1
  simplification per spec ("ad_* grouped is acceptable v1").
- **Consent renewal**: stored consent expires after `data-expiry-days`
  (default 180) and the banner re-asks. This is an addition beyond the
  literal spec (CNIL best-practice, not explicitly requested) — flagged
  below for gemini to confirm the 180-day default is the right cadence.
- **Link to more information**: banner copy always links to
  `data-privacy-url`.

## Strict-CSP compatibility (`script-src 'self'`)

- Zero inline `<script>` blocks, zero `onclick="…"`/inline event-handler
  attributes anywhere in `consent-banner.js` or the banner markup it builds.
  Every handler is wired with `addEventListener` from the external file.
- `consent-banner.js` builds all DOM nodes with `document.createElement` /
  `textContent` / `setAttribute` — no `innerHTML`, so there's no injection
  surface even though all copy here is static, developer-authored text (not
  user input).
- Configuration travels via `data-*` attributes on the `<script>` tag
  (read through `document.currentScript.dataset`), not an inline config
  object, so a site never needs an inline `<script>` to configure this
  component.
- `consent-banner.css` is a plain external stylesheet; no `style="…"`
  attributes are set from JS (CSS classes are toggled instead), so this also
  works under `style-src 'self'` with no `'unsafe-inline'`.

## Accessibility

- All interactive controls are real `<button>` / `<input type="checkbox">` +
  `<label for>` elements — native keyboard support (Tab / Space / Enter) and
  screen-reader semantics for free, no custom ARIA widget reimplementation.
- Visible focus ring on every control (`:focus-visible`, using `outline`,
  not just a color/shadow change, so it survives a host site's own resets).
- The banner is inserted as the **first** child of `<body>` (it's
  fixed-position via CSS so this doesn't affect visual layout), so keyboard
  users reach the consent choice before the rest of the page's interactive
  content, and `aria-live="polite"` + `role="region"` on the container
  announces it to screen readers without stealing focus or trapping it
  (deliberately not a focus-trapping modal — CNIL prohibits blocking access
  to the site pending a cookie decision).
- Toggle switches are real checkboxes, visually restyled (see
  `.swc-toggle-input` in the CSS) but never `display:none`'d, so they stay
  focusable and are announced by screen readers as checkboxes with their
  label text.

## Theming

Every color is a CSS custom property with a default baked into
`#swarph-consent-banner` in `consent-banner.css` (`--swc-bg-solid`,
`--swc-fg`, `--swc-accent`, `--swc-accent-fg`, `--swc-muted`, `--swc-border`,
`--swc-focus`, `--swc-radius`). A site can retheme without touching the JS
or CSS file by overriding these on `:root` or `#swarph-consent-banner` in
its own stylesheet, loaded after `consent-banner.css`.

## Reopening the banner later ("Manage cookies" footer link)

`consent-banner.js` exposes `window.SwarphConsent.open()`. A site can wire a
persistent footer link/button to it with its own small external script
(again, no inline handler):

```js
document.getElementById('manage-cookies-link')
  .addEventListener('click', function () { window.SwarphConsent.open(); });
```

## Testing

There's no build/test tooling in this repo (static, no-build site) and no
browser test runner installed, so verification here is two-layered:

1. **Headless self-check** (`node web/consent/selfcheck.js`) — loads the
   *actual* `consent-default.js` and `consent-banner.js` source files with
   Node's built-in `vm` module against a small hand-rolled DOM/localStorage
   stub (zero new dependencies) and asserts: the default-denied push shape,
   Accept/Reject/Save all push the right `consent update` and persist it,
   toggles default to unchecked, a valid stored choice replays *before*
   `DOMContentLoaded* and suppresses the banner, and both consent expiry and
   a `policyVersion` bump correctly force re-consent. Run it after any
   change to either file. As of this writing, all 8 checks pass.
2. **Manual real-browser check** (`web/consent/test.html`) — open it
   directly (or serve `web/` and browse to `/consent/test.html`); it logs
   every `dataLayer` push live and includes a QA checklist (keyboard nav,
   equal Accept/Reject prominence, no pre-ticked toggles, persistence across
   reload). This was also driven once end-to-end with Playwright during
   development (first-visit render → Manage preferences → toggle Analytics
   on → Save → reload replays `analytics_storage: granted` before any
   banner shows → reset button returns to the first-visit state) to confirm
   real-DOM behavior beyond what the Node stub can exercise.

## Known v1 scope / things for gemini to double-check

- **`ad_*` grouped**: `ad_storage`, `ad_user_data`, and `ad_personalization`
  are always granted/denied together as one "Advertising" toggle, per spec.
  If any downstream site needs to split these (e.g. remarketing vs. ad
  personalization as separate choices), that's a v2 change to
  `CATEGORY_KEYS` in `consent-banner.js`.
- **180-day expiry** is an addition beyond the literal spec, not something
  gemini explicitly asked for — please confirm the cadence (or turn it off
  by passing a very large `data-expiry-days`).
- **No "X"/dismiss control** on the banner by design (see CNIL section
  above) — confirm this reads as correct rather than as a missing feature.
- **`/privacy` doesn't exist yet** on swarph.ai in this repo. The banner
  links to whatever `data-privacy-url` is configured to; each site owner
  needs an actual privacy/cookie policy page there before this ships live.
- This component does **not** edit any site's HTML or deploy anything — per
  the task, that's the orchestrator's job once this is reviewed.
