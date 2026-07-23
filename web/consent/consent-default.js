/*!
 * swarph — Consent Mode v2 default state (Basic Consent Mode)
 * Card #91. Owner-spec: gemini (GA4/GTM authority).
 *
 * MUST be the very first script in <head>, loaded BEFORE the GTM/GA
 * container snippet and before consent-banner.js. Plain classic <script src>
 * — no defer, no async — so it runs synchronously in document order and the
 * default below is guaranteed to be pushed to dataLayer before any tag fires.
 *
 * This is the external-file twin of the inline snippet in README.md, for
 * strict-CSP sites (script-src 'self') that cannot use an inline <script>.
 * The body below is byte-for-byte the snippet gemini specified — do not
 * "improve" or wrap it; GTM's own docs show this exact unwrapped shape and
 * downstream tooling may diff against it.
 */
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('consent','default',{'ad_storage':'denied','analytics_storage':'denied','ad_user_data':'denied','ad_personalization':'denied'});
