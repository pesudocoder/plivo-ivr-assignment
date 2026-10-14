"""All spoken IVR text, shared by the routes and the tests."""

# Plivo <Speak> language/voice per IVR language code.
SPEAK_VOICES = {
    "en": {"language": "en-US", "voice": "WOMAN"},
    "es": {"language": "es-US", "voice": "WOMAN"},
}

# OTP stage (Level 0), always spoken in Plivo's default voice.
OTP_PROMPTS = {
    "welcome": "Welcome to the InspireWorks demo. Please enter your 4-digit OTP.",
    "no_input": "We did not receive any input.",
    "incorrect": "Incorrect OTP. Please try again.",
    "verified": "Thank you. You have been verified.",
}

# Level 1: each option is spoken in its own language.
LANGUAGE_MENU = {
    "en": "For English, press 1.",
    "es": "Para español, presione 2.",
}
LANGUAGE_MENU_INVALID = "Invalid option."

# Level 2, spoken in the language chosen at Level 1.
ACTION_PROMPTS = {
    "en": {
        "menu": "Press 1 to hear a short audio message. Press 2 to speak with a live associate.",
        "connecting": "Connecting you to an associate.",
        "unavailable": "The associate is unavailable. Goodbye.",
        "goodbye": "Thank you for calling. Goodbye.",
        "invalid": "Invalid option.",
    },
    "es": {
        "menu": "Presione 1 para escuchar un mensaje de audio. Presione 2 para hablar con un asociado.",
        "connecting": "Conectándolo con un asociado.",
        "unavailable": "El asociado no está disponible. Adiós.",
        "goodbye": "Gracias por llamar. Adiós.",
        "invalid": "Opción no válida.",
    },
}
