# Requirements Traceability

Status values: Pending / Pass / Fail / Manual-pending. Updated at the end of each phase.

| ID | Requirement | Phase | Verified by (test name or manual step) | Status |
|----|-------------|-------|----------------------------------------|--------|
| R1 | Outbound call from the Plivo number (PLIVO_FROM_NUMBER) to the target number via an endpoint or script | 2 | `test_r1_call_uses_plivo_from_number_and_target`, `test_r1_answer_and_hangup_urls_built_from_public_base_url`, `test_r1_base_url_trailing_slash_not_doubled`, `test_r1_returns_request_uuid`, `test_cli_prints_request_uuid`. Note: a live call is verified manually in Phase 6 (see "Manual live check (Phase 2)") | Pass |
| R2 | Target number configurable via simple UI or config variable | 2 | `test_r2_target_defaults_to_config_target_number`, `test_r2_target_overridable_via_request_body`, `test_r2_invalid_number_rejected_400`, `test_r2_non_object_body_rejected_400`, `test_r2_cli_to_flag_overrides_target` | Pass |
| R3 | On answer, prompt caller to enter a 4-digit OTP via DTMF | 3 | | Pending |
| R4 | OTP is hardcoded birthdate in DDMM format | 3 | | Pending |
| R5 | Wrong OTP → re-prompt until correct OTP entered | 3 | | Pending |
| R6 | IVR menu accessible only after correct OTP | 3 | | Pending |
| R7 | Level 1: Press 1 English, Press 2 Spanish | 4 | | Pending |
| R8 | Level 2 Press 1: play a publicly hosted MP3 | 4 | | Pending |
| R9 | Level 2 Press 2: forward call to associate number (ASSOCIATE_NUMBER) | 4 | | Pending |
| R10 | Level 2 prompts are spoken in the language chosen at Level 1 | 4 | | Pending |
| R11 | Call flow uses Plivo XML | 4 | `test_r11_answer_returns_valid_plivo_xml` | Partial (placeholder /answer) |
| R12 | DTMF handled correctly across all levels (OTP, language, action) | 4 | | Pending |
| R13 | Branching logic based on user input | 4 | | Pending |
| R14 | Invalid input (wrong key, no input/timeout) repeats the current prompt | 4 | | Pending |
| R15 | Optional frontend: simple web page or CLI to trigger the call | 5 | | Pending |
| R16 | README: setup instructions, required Plivo credentials (Auth ID / Auth Token), steps to run and test | 6 | | Pending |
| R17 | Demo video 3–5 min: call made, wrong OTP then correct OTP, Level 1 → Level 2, audio playback, call forwarding (manual) | 6 | | Pending |
| R18 | Receiver phone number included in submission email (manual) | 6 | | Pending |

## Manual live check (Phase 2)

Places a real call; not part of the automated suite. Activate `.venv` first.

1. Run the server: `python run.py`
2. In a second terminal, expose it: `ngrok http 5000`
3. Copy the https forwarding URL from ngrok into `PUBLIC_BASE_URL` in `.env`
4. Restart the server so it picks up the new `PUBLIC_BASE_URL`
5. Place the call: `python scripts/make_call.py` (optionally `--to +91XXXXXXXXXX`)
6. Confirm the phone rings and, on answer, plays "Hello from the Plivo IVR demo. Setup is working." and then hangs up
