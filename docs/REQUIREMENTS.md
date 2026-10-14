# Requirements Traceability

Status values: Pending / Pass / Fail / Manual-pending. Updated at the end of each phase.

| ID | Requirement | Phase | Verified by (test name or manual step) | Status |
|----|-------------|-------|----------------------------------------|--------|
| R1 | Outbound call from the Plivo number (PLIVO_FROM_NUMBER) to the target number via an endpoint or script | 2 | `test_r1_call_uses_plivo_from_number_and_target`, `test_r1_answer_and_hangup_urls_built_from_public_base_url`, `test_r1_base_url_trailing_slash_not_doubled`, `test_r1_returns_request_uuid`, `test_cli_prints_request_uuid`. Note: a live call is verified manually in Phase 6 (see "Manual live check (Phase 2)") | Pass |
| R2 | Target number configurable via simple UI or config variable | 2 | `test_r2_target_defaults_to_config_target_number`, `test_r2_target_overridable_via_request_body`, `test_r2_invalid_number_rejected_400`, `test_r2_non_object_body_rejected_400`, `test_r2_cli_to_flag_overrides_target` | Pass |
| R3 | On answer, prompt caller to enter a 4-digit OTP via DTMF | 3 | `test_r3_answer_prompts_for_4_digit_dtmf`, `test_r3_no_input_reprompts_via_redirect_to_answer`, `test_r3_redirect_urls_absolute_with_trailing_slash_base` | Pass |
| R4 | OTP is hardcoded birthdate in DDMM format | 3 | `test_r4_correct_otp_matches_birthdate_config`, `test_r4_correct_otp_redirects_to_language_menu`, `test_birthdate_otp_is_four_digit_ddmm`, `test_otp_value_never_in_xml_or_logs` | Pass |
| R5 | Wrong OTP → re-prompt until correct OTP entered | 3 | `test_r5_wrong_otp_reprompts`, `test_r5_repeated_wrong_otps_keep_reprompting`, `test_r5_empty_short_long_and_nonnumeric_otp_rejected`, `test_r5_missing_digits_param_rejected` | Pass |
| R6 | IVR menu accessible only after correct OTP | 3 | `test_r6_menu_without_auth_redirects_to_answer`, `test_r6_menu_without_call_uuid_redirects_to_answer`, `test_r6_menu_after_auth_allowed`, `test_r6_auth_is_per_call`, `test_r6_hangup_clears_auth` | Pass |
| R7 | Level 1: Press 1 English, Press 2 Spanish | 4 | `test_r7_language_menu_offers_english_1_and_spanish_2`, `test_r7_press_1_selects_english`, `test_r7_press_2_selects_spanish` | Pass |
| R8 | Level 2 Press 1: play a publicly hosted MP3 | 4 | `test_r8_action_1_plays_public_mp3`, `test_r8_audio_url_overridable`, `test_r8_audio_url_defaults_to_public_mp3_and_is_overridable`; default URL HEAD-checked manually (200, audio/mp3) | Pass |
| R9 | Level 2 Press 2: forward call to associate number (ASSOCIATE_NUMBER) | 4 | `test_r9_action_2_dials_associate_number`, `test_r9_associate_number_normalized`, `test_r9_missing_associate_number_speaks_unavailable` | Pass |
| R10 | Level 2 prompts are spoken in the language chosen at Level 1 | 4 | `test_r10_level2_prompts_in_english`, `test_r10_level2_prompts_in_spanish`, `test_r10_language_is_per_call` | Pass |
| R11 | Call flow uses Plivo XML | 4 | `test_r11_answer_returns_valid_plivo_xml`, `test_r11_all_menu_responses_are_valid_plivo_xml`, `test_r3_answer_prompts_for_4_digit_dtmf` | Pass |
| R12 | DTMF handled correctly across all levels (OTP, language, action) | 4 | `test_r12_dtmf_handled_at_every_level` | Pass |
| R13 | Branching logic based on user input | 4 | `test_r13_full_flow_english_audio_then_forward`, `test_r13_full_flow_spanish` | Pass |
| R14 | Invalid input (wrong key, no input/timeout) repeats the current prompt | 4 | `test_r14_invalid_language_key_repeats_level1`, `test_r14_invalid_action_key_repeats_level2_in_chosen_language`, `test_r14_no_input_repeats_each_level`, `test_r3_no_input_reprompts_via_redirect_to_answer` | Pass |
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

## Manual live check (Phase 3)

Places a real call; not part of the automated suite. Activate `.venv` first.

1. Start the server: `python run.py`
2. In a second terminal: `ngrok http 5000`
3. Confirm `PUBLIC_BASE_URL` in `.env` matches the current ngrok https URL (free ngrok URLs change on every restart); if you edit it, restart the server
4. Place the call: `python scripts/make_call.py`
5. On answer, hear "Welcome to the InspireWorks demo. Please enter your 4-digit OTP."
6. Enter a WRONG 4-digit OTP → hear "Incorrect OTP. Please try again." and the prompt repeats
7. Enter the correct OTP → hear "Thank you. You have been verified." then "Authentication complete. The menu will be added in the next phase." and the call hangs up
8. Optional: stay silent at the prompt for ~10s → hear "We did not receive any input." and the prompt repeats

## Manual live check (Phase 4)

Places real calls; not part of the automated suite. Activate `.venv`, start `python run.py` and `ngrok http 5000`, and confirm `PUBLIC_BASE_URL` in `.env` matches the current ngrok https URL (restart the server after editing it).

**Call 1 (English):** `python scripts/make_call.py`

1. Enter the correct OTP → hear "Thank you. You have been verified."
2. Hear "For English, press 1." / "Para español, presione 2." → press 1
3. Hear the English Level 2 prompt → press 9 → hear "Invalid option." and the Level 2 prompt repeats
4. Press 1 → the MP3 plays, then the Level 2 prompt returns
5. Press 2 → hear "Connecting you to an associate." and the associate number (ASSOCIATE_NUMBER) rings

**Call 2 (Spanish):** `python scripts/make_call.py`

1. Enter the correct OTP → press 2 at the language menu
2. Hear the Level 2 prompt in Spanish: "Presione 1 para escuchar un mensaje de audio. Presione 2 para hablar con un asociado."
3. Press 1 → the MP3 plays, then the Spanish Level 2 prompt returns
