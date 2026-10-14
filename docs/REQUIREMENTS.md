# Requirements Traceability

Status values: Pending / Pass / Fail / Manual-pending. Updated at the end of each phase.

| ID | Requirement | Phase | Verified by (test name or manual step) | Status |
|----|-------------|-------|----------------------------------------|--------|
| R1 | Outbound call from the Plivo number (PLIVO_FROM_NUMBER) to the target number via an endpoint or script | 2 | | Pending |
| R2 | Target number configurable via simple UI or config variable | 2 | | Pending |
| R3 | On answer, prompt caller to enter a 4-digit OTP via DTMF | 3 | | Pending |
| R4 | OTP is hardcoded birthdate in DDMM format | 3 | | Pending |
| R5 | Wrong OTP → re-prompt until correct OTP entered | 3 | | Pending |
| R6 | IVR menu accessible only after correct OTP | 3 | | Pending |
| R7 | Level 1: Press 1 English, Press 2 Spanish | 4 | | Pending |
| R8 | Level 2 Press 1: play a publicly hosted MP3 | 4 | | Pending |
| R9 | Level 2 Press 2: forward call to associate number (ASSOCIATE_NUMBER) | 4 | | Pending |
| R10 | Level 2 prompts are spoken in the language chosen at Level 1 | 4 | | Pending |
| R11 | Call flow uses Plivo XML | 4 | | Pending |
| R12 | DTMF handled correctly across all levels (OTP, language, action) | 4 | | Pending |
| R13 | Branching logic based on user input | 4 | | Pending |
| R14 | Invalid input (wrong key, no input/timeout) repeats the current prompt | 4 | | Pending |
| R15 | Optional frontend: simple web page or CLI to trigger the call | 5 | | Pending |
| R16 | README: setup instructions, required Plivo credentials (Auth ID / Auth Token), steps to run and test | 6 | | Pending |
| R17 | Demo video 3–5 min: call made, wrong OTP then correct OTP, Level 1 → Level 2, audio playback, call forwarding (manual) | 6 | | Pending |
| R18 | Receiver phone number included in submission email (manual) | 6 | | Pending |
