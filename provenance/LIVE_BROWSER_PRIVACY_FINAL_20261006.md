# HUNTER v0.7.23 — final normal-browser privacy/usability assessment

Date: 2026-10-06  
Production URL: https://hunter.goyal-lab.org/  
Status: **PASS**

## Chrome direct workflow — PASS

Fresh normal headed Chrome 154 profile:
- production page HTTP 200;
- one-click Load example loaded 10 records in Detailed report mode;
- HUNTER completed analysis of all 10 records;
- results table contained header + 10 records;
- TSV download `HUNTER_v1_results.tsv` completed (9,240 bytes);
- no Local Storage entries;
- no Session Storage entries;
- no service workers;
- no console errors;
- no non-200 HUNTER workflow responses;
- no third-party HTTP(S) web requests observed during the audited workflow.

The only cookie visible for the HUNTER origin was:
- `hcdn`
- domain: `hunter.goyal-lab.org`
- session cookie;
- HttpOnly;
- Secure;
- SameSite=None.

It is classified as a Hostinger CDN first-party browser-verification/security session cookie. It is not set by HUNTER application code and is not a HUNTER analytics/tracking cookie.

## Parent site → HUNTER transition — PASS

A separate fresh Chrome profile was opened first at `https://goyal-lab.org/`.

Parent-site snapshot:
- no cookies present;
- no Local Storage;
- one WordPress emoji capability entry in Session Storage (`wpEmojiSettingsSupports`);
- no service-worker controller.

After navigating to HUNTER:
- the HUNTER origin contained only the Hostinger `hcdn` session/security cookie;
- HUNTER Local Storage was empty;
- HUNTER Session Storage was empty;
- `document.cookie` was empty because the Hostinger cookie is HttpOnly;
- no HUNTER service-worker controller was present.

Thus the HUNTER application does not inherit a parent-domain tracking cookie in this fresh-profile test.

## Second installed browser — Microsoft Edge — PASS

Fresh normal headed Edge 154:
- production page HTTP 200;
- Load example loaded 10 records in Detailed mode;
- all 10 records completed;
- results table contained header + 10 records;
- TSV download completed (9,240 bytes);
- Local Storage empty;
- Session Storage empty;
- no service-worker controller;
- no console errors;
- only the same first-party Hostinger `hcdn` session/security cookie was present.

The initial automated host list also included two `chrome-extension://`/browser-extension scheme identifiers. These are browser-internal extension requests, not third-party HTTP(S) web destinations and are therefore excluded from the web-network privacy assessment.

## Conclusion

The production HUNTER application passes the normal-browser usability/privacy gate on the two installed Chromium-family desktop browsers tested. No HUNTER application tracking/storage mechanism was detected. The Hostinger `hcdn` session cookie should be described, if needed, as hosting/CDN security infrastructure rather than HUNTER analytics.

This browser assessment, together with the previously passed production scientific parity, download, integrity and performance gates, closes the v0.7.23 production-release certification.

## Protected boundary

No scientific model, manuscript, figure, legend, H5/HPS reference file or threshold was changed during browser testing.
