# Demo Video Script (3–5 minutes)

Covers R17: the call being made, a wrong OTP then the correct OTP, Level 1 → Level 2, audio playback, and call forwarding.

## Pre-recording checklist

- [ ] `.venv` active and `python run.py` running (port 5000)
- [ ] `ngrok http 5000` running in a second terminal
- [ ] `PUBLIC_BASE_URL` in `.env` matches the **current** ngrok https URL, and the server was restarted after any change
- [ ] `curl http://127.0.0.1:5000/health` returns `{"status": "ok"}`
- [ ] Target phone and associate phone are both nearby, charged, and (on a Plivo trial) verified as sandbox numbers
- [ ] Target phone on **speaker**, close to the recording mic, so prompts and the MP3 are audible
- [ ] Screen recorder capturing the browser and terminals, with audio from the mic
- [ ] Editor and terminals don't show `.env`, the Auth Token, or the OTP value
- [ ] Terminal ready to run `pytest -v` at the end
- [ ] Do a dry run of the call once before recording

## Script

| Time | On screen | Action / narration |
|------|-----------|--------------------|
| 0:00–0:25 | README in the editor or on GitHub | "This is a Plivo voice IVR demo built with Flask. It places an outbound call, verifies a 4-digit OTP via the keypad, then runs a two-level menu in English or Spanish. Every step is Plivo XML." Briefly show the call flow diagram. |
| 0:25–0:45 | Project tree | "The app is in `app/`: the Plivo client, the XML webhooks in `routes/ivr.py`, and the prompts. Tests are in `tests/`, and `docs/REQUIREMENTS.md` traces every requirement to a test." |
| 0:45–1:05 | Terminals: `python run.py` and `ngrok http 5000` | "The server runs locally, and ngrok exposes it so Plivo can fetch the webhooks." |
| 1:05–1:20 | Browser at http://127.0.0.1:5000 | "The call is triggered from this local page. The number is configurable and pre-filled from config." Click **Start Call** and show the request UUID. |
| 1:20–1:35 | Phone (speaker) | Phone rings; answer. Prompt: "Welcome to the InspireWorks demo. Please enter your 4-digit OTP." |
| 1:35–1:55 | Phone | "First a **wrong** OTP." Enter wrong digits and hear "Incorrect OTP. Please try again." and the prompt repeats. |
| 1:55–2:10 | Phone | "Now the correct OTP, my birthdate as DDMM." Enter it (don't say it aloud) and hear "Thank you. You have been verified." |
| 2:10–2:30 | Phone | Level 1: "For English, press 1. Para español, presione 2." Press **1**. |
| 2:30–2:45 | Phone | Level 2 in English: "Press 1 to hear a short audio message. Press 2 to speak with a live associate." |
| 2:45–3:10 | Phone | Press **1**. The hosted MP3 plays (let ~10 s play), then the Level 2 menu returns. |
| 3:10–3:45 | Phone + associate phone | Press **2** and hear "Connecting you to an associate." The associate phone rings; answer it and say a few words to show the call is bridged. Hang up and hear "Thank you for calling. Goodbye." |
| 3:45–4:15 | *(Optional)* Phone | Quick second call: correct OTP → press **2** and hear the Spanish Level 2 prompt "Presione 1 para escuchar un mensaje de audio…". Hang up. |
| 4:15–4:45 | Terminal | Run `pytest -v`; scroll to "135 passed". "The suite mocks Plivo, so it runs offline. It covers every level, invalid keys, timeouts, and the OTP gate." |
| 4:45–5:00 | `docs/REQUIREMENTS.md` | "Every requirement maps to a test or a manual step. Thanks for watching." |

## Tips

- If a step goes wrong (for example ngrok was restarted), stop and fix `PUBLIC_BASE_URL` before recording again rather than editing around it.
- Keep keypresses deliberate; pause after each prompt finishes so the DTMF tones are clearly audible.
- If the associate doesn't answer, the caller hears "The associate is unavailable. Goodbye." This is correct behavior, but answering shows the forwarding better.
