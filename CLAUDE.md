# CLAUDE.md

Plivo voice IVR demo (technical assignment). A Flask app triggers an outbound call via Plivo's Python SDK; Plivo fetches Plivo XML from our webhooks (exposed via ngrok). Flow: OTP via DTMF → Level 1 language menu → Level 2 action menu.

## Rules

- The user commits via GitHub Desktop on a per-phase branch. Never run `git commit`, `git push`, `git checkout`, `git branch`, or any `gh` command. Read-only git (e.g. `git status`) is fine.
- Never print or commit `.env`. Config comes from env vars via python-dotenv (`run.py` loads `.env`; `app/config.py` reads `os.environ`).
- Activate `.venv` before installing or running anything (`source .venv/Scripts/activate` in Git Bash, `.venv\Scripts\Activate.ps1` in PowerShell).

## Testing

- Tests never hit the real Plivo API or the network; mock the Plivo client.
- Test names include the requirement ID where one applies, e.g. `test_r5_wrong_otp_reprompts`.
- `tests/conftest.py` provides `app` and `client` fixtures with fake config and clears real credential env vars.

## End of every phase: verification

1. Run the full suite: `pytest -v`.
2. Update `docs/REQUIREMENTS.md` status (Pass / Fail / Manual-pending) for that phase's requirements, citing the test names that verify each one.
3. Run `git status` and confirm `.env` and `.venv/` are not listed.
4. Give a short verification report and a one-line conventional commit message, then stop.

## Layout

- `app/__init__.py` — `create_app(test_config=None)` factory
- `app/config.py` — env loading, `BIRTHDATE_OTP`, `require_call_config()` (raises `MissingCredentialsError`)
- `app/routes/` — blueprints (`/health`, later the call and IVR webhooks)
- `run.py` — dev server on port 5000
- `docs/REQUIREMENTS.md` — requirements traceability table
