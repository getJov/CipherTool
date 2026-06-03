# Enhance CipherTool UI/UX

## Why
Users can technically log in, encrypt/decrypt messages, and generate QR codes, but the current interface does not clearly explain that workflow. Improving the UI now makes the app easier to understand without changing the core cipher/auth behavior.

## What
Redesign the existing server-rendered screens so CipherTool clearly guides users through login, verification, message encryption/decryption, and QR creation while preserving the current mint/teal/navy color palette. Done means the main screens are visually consistent, responsive, easier to scan, and the QR flow can support including an encrypted message in the generated QR content.

## Context

**Relevant files:**
- `templates/login.html` - local login entry screen and Google login link.
- `templates/register.html` - account creation screen.
- `templates/googleAuth.html` - TOTP QR verification screen after login.
- `templates/cipher.html` - primary encrypt/decrypt workspace.
- `templates/myQR.html` - QR generation page.
- `static/style.css` - shared visual system and responsive layout rules.
- `static/app.js` - cipher-specific field visibility behavior.
- `static/password.js` - password visibility toggles.
- `app.py` - route data passed into cipher and QR templates.
- `static/ctL.png` and `static/ctL.ico` - existing brand assets.

**Patterns to follow:**
- Keep Flask server-rendered templates and the current static CSS/JS structure.
- Keep the existing palette anchored on `#61d2b4`, `#367591`, `#152744`, `#263849`, and `#f0f0f0`.
- Use existing Font Awesome icons already loaded by the templates.
- Keep the current route names and form submission model.

**Key decisions already made:**
- No new frontend framework, component library, or build step.
- The cipher page becomes the main workspace after login.
- QR generation should feel connected to encrypted-message sharing, not only contact-card creation.
- This is a UI/UX enhancement, not a cipher algorithm rewrite or auth rewrite.

## Constraints

**Must:**
- Preserve the existing app colors while improving contrast, hierarchy, spacing, and responsive behavior.
- Make the intended workflow understandable from the screens themselves: login, verify, encrypt/decrypt, create QR.
- Improve the cipher screen with clearer labels, grouped controls, mode selection, result handling, and copy affordance.
- Improve the QR screen so users can include encrypted message content when creating a QR code.
- Prefill the QR message field from the latest cipher result when the user chooses the QR action after generating a result.
- Keep existing auth, cipher, and QR routes stable unless a small route/template data addition is required for the QR workflow.
- Keep forms usable on mobile and desktop without horizontal overflow.
- Verify responsive behavior at a minimum of 375px mobile width and a standard desktop width.
- Preserve password toggle and cipher key/keyword visibility behavior.
- Keep changes scoped to UI/UX and the minimum supporting route/template data.

**Must not:**
- Do not introduce new dependencies.
- Do not add a frontend build pipeline.
- Do not redesign the color palette into a new brand.
- Do not refactor Flask routing into blueprints or services.
- Do not change cipher algorithm behavior.
- Do not change database schema.
- Do not remove existing QR contact/detail fields; make them optional and visually secondary to encrypted-message QR content.
- Do not mix in unrelated security/auth cleanup.
- Do not modify unrelated local-run or environment setup work.

**Out of scope:**
- Production security hardening.
- Replacing classic ciphers with modern cryptography.
- QR scanning.
- User QR history/storage.
- Database-backed saved messages.
- Full accessibility certification.
- New authentication providers.

## Risk

**Level:** 2

**Risks identified:**
- The current QR page is product-mismatched because it generates contact-style QR data while the requested experience includes encrypted-message QR sharing -> **Mitigation:** keep existing optional contact fields but add encrypted-message support and copy that clarifies the QR can carry message content.
- UI-only changes can accidentally hide required form fields or break existing POST expectations -> **Mitigation:** keep field names and route actions stable; only reorganize markup around the same server contract unless explicitly noted.
- The current CSS uses fixed widths and `100vh`, which can cause mobile overflow -> **Mitigation:** replace fragile layout rules with responsive constraints and verify login, register, verifier, cipher, and QR pages at mobile and desktop widths.
- Result-to-QR handoff may require a small data-flow addition from the cipher result to the QR page -> **Mitigation:** add a QR action on the cipher result that opens the QR page with the encrypted result available to prefill the QR message field, using the smallest route/template data change available.

**Pushback (if any):**
- The QR page should not stay as a disconnected contact-card tool if the product promise is encrypted-message sharing. That drift makes the app harder to explain. The better design is to keep contact details optional and make the encrypted message the primary QR payload when available.
- The current UI relies on placeholder text instead of real labels. That looks compact, but it is hostile to comprehension. Future-us should not debug user confusion caused by unlabeled controls.

## Tasks

### T1: Establish shared visual structure
**Do:** Update the shared layout and component styling so all screens use consistent containers, headers, form groups, labels, buttons, alerts, account controls, and responsive spacing while preserving the existing palette.
**Files:** `static/style.css`
**Verify:** Manual: login, register, verifier, cipher, and QR pages share the same visual language and do not overflow at 375px mobile width or standard desktop width.

### T2: Clarify authentication and verification screens
**Do:** Improve login, register, and Google Authenticator screens with clearer headings, short workflow-oriented copy, better form labeling, stronger error/alert placement, and cleaner action hierarchy.
**Files:** `templates/login.html`, `templates/register.html`, `templates/googleAuth.html`, `static/style.css`, `static/password.js`
**Verify:** Manual: local login, register, Google login link, password toggles, and authenticator entry remain usable.

### T3: Redesign the cipher workspace
**Do:** Rework the cipher page into a clear encrypt/decrypt workspace with visible mode selection, cipher selection, conditional key/keyword field, message input, result panel, copy action, account/logout controls, and a QR action that sends the latest result to the QR page for prefill.
**Files:** `templates/cipher.html`, `static/style.css`, `static/app.js`, `app.py`
**Verify:** Manual: Atbash, Caesar, and Vigenere encryption/decryption still submit correctly; result copy still works; QR action opens the QR page with the latest result available.

### T4: Align QR generation with encrypted-message sharing
**Do:** Redesign the QR page so encrypted message content is easy to include and can be prefilled from the cipher result, optional contact fields are secondary, preview/download are clear, and empty/generated states are understandable.
**Files:** `templates/myQR.html`, `static/style.css`, `app.py`
**Verify:** Manual: QR generation still creates `static/myQR.png`; generated QR can include encrypted message content when supplied or prefilled from the cipher page; download button still downloads the QR image.

### T5: Verify responsive behavior and browser runtime
**Do:** Run available project checks and manually inspect key screens for layout overflow, broken controls, missing labels, and console errors.
**Files:** `templates/login.html`, `templates/register.html`, `templates/googleAuth.html`, `templates/cipher.html`, `templates/myQR.html`, `static/style.css`, `static/app.js`, `static/password.js`
**Verify:** `python -m py_compile app.py`; manual: browser pages load without obvious JavaScript errors; 375px mobile and desktop layouts remain readable with no horizontal scrolling.

## Done
- [ ] Existing color palette is preserved and used consistently.
- [ ] Login/register screens explain the app purpose before users enter the tool.
- [ ] Authenticator screen clearly communicates the verification step.
- [ ] Cipher screen clearly supports encrypt and decrypt modes.
- [ ] Cipher-specific key/keyword controls remain conditional and understandable.
- [ ] Cipher result is displayed in a dedicated, copyable result area.
- [ ] Users have a clear path from encrypted output to QR generation.
- [ ] QR message field is prefilled from the latest cipher result when opened from a cipher result action.
- [ ] QR page supports including encrypted message content.
- [ ] QR contact/detail fields remain optional and secondary.
- [ ] QR preview and download affordances are clear.
- [ ] No horizontal overflow at 375px mobile width.
- [ ] Desktop layout remains readable and balanced at a standard desktop width.
- [ ] No new dependencies or frontend build tooling.
- [ ] Existing route names and form field contracts remain stable unless the spec is revised.
- [ ] `python -m py_compile app.py` passes.
- [ ] Manual login/register/verifier/cipher/QR smoke check passes.

## Revision Log

### Rev 1 - 2026-06-04
**Change:** Added concrete responsive verification requirements and explicit cipher-result-to-QR prefill behavior.
**Reason:** User requested stronger responsiveness coverage, and the previous spec-governance review identified QR handoff ambiguity.
**Updated Done criteria:** Added 375px mobile and desktop layout checks, plus QR message prefill from the latest cipher result.
