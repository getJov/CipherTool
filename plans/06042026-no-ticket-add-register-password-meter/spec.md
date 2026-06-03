# Add Register Password Controls

## Why
The register page accepts passwords with specific complexity rules, but users do not get enough immediate feedback while typing. Adding explicit show/hide controls and a password strength meter reduces failed submissions without changing server-side validation.

## What
Enhance the register page with visible Show/Hide password buttons for both password fields and a client-side password meter for the primary password. Done means users can toggle password visibility, see password strength feedback while typing, and existing registration field names/routes still work.

## Context

**Relevant files:**
- `templates/register.html` - register form markup.
- `static/password.js` - password visibility behavior.
- `static/style.css` - shared auth form and meter styles.
- `app.py` - existing server-side password validation remains the source of truth.

**Patterns to follow:**
- Keep Flask templates and static JS/CSS.
- Keep existing field IDs and names: `password`, `confirm-password`, `confirm-password`.
- Use existing palette and auth page styling.

**Key decisions already made:**
- No new dependencies.
- Client meter is guidance only; server validation remains unchanged.

## Constraints

**Must:**
- Add visible Show/Hide controls on the register password and confirm password fields.
- Add a password meter on the register page that updates while typing.
- Keep existing password validation in `app.py` unchanged.
- Keep login page password toggle behavior working.
- Keep layout responsive and avoid overflow at 375px width.

**Must not:**
- Do not change registration route names, field names, or database behavior.
- Do not add dependencies.
- Do not weaken password requirements.
- Do not add password meter to login unless needed for shared script safety.

**Out of scope:**
- Server-side password policy changes.
- Account recovery.
- Accessibility certification.

## Risk

**Level:** 1

**Risks identified:**
- Password meter could imply acceptance when server validation still fails -> **Mitigation:** meter text must say what is missing and not replace server validation.

**Pushback (if any):**
- None.

## Tasks

### T1: Add register password controls
**Do:** Update register markup with explicit Show/Hide buttons and a password meter region.
**Files:** `templates/register.html`, `static/style.css`
**Verify:** Manual: register form shows both visibility buttons and the meter without overflow.

### T2: Wire password meter and toggles
**Do:** Update password script to support button text/icon state and live strength feedback, while preserving login toggle behavior.
**Files:** `static/password.js`
**Verify:** Manual: typing in register password updates meter; toggles work on login and register.

## Done
- [ ] Register password and confirm password fields have visible Show/Hide controls.
- [ ] Register password meter updates while typing.
- [ ] Meter gives missing-requirement feedback without changing server validation.
- [ ] Login password toggle still works.
- [ ] No new dependencies.
- [ ] `python -m py_compile app.py` or available equivalent passes.
- [ ] Register page renders successfully.
