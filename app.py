import streamlit as st
# Mental Wellness Support Bot
"""
Mental Wellness Support Bot
---------------------------
A conversational Python bot to guide users through a mental wellness check-in, recommend coping strategies, and provide supportive resources.

Features:
- Friendly conversational flow with text-to-speech (British accent) for accessibility and warmth.
- Reflective listening and summarization.
- Crisis detection with immediate resource guidance.
- Personalized strategy recommendations based on user check-in.
- Modular, extensible codebase.

"""

# Imports
# We bring in various tools to help the bot work smoothly:
# - typing: helps us specify the kind of data we're working with (like lists or dictionaries).
# - textwrap: makes printed text look neat by wrapping long lines.
# - platform: lets us find out which operating system we're on (Windows, Mac, Linux).
# - subprocess and shutil: help us run other programs on the computer, like speaking text aloud.
# - re: helps us find and remove certain parts of text (like hints in parentheses).
# - pyttsx3 (if available): a library to turn text into speech so the bot can talk to you.
import typing as t
import textwrap
import platform
import subprocess
import shutil
import re
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

# TTS (British accent) configuration
# _TTS_ENGINE will hold the text-to-speech engine if we can start it.
# We check what operating system we're on because speaking text aloud works differently on each.
_TTS_ENGINE = None
_TTS_IS_MAC = platform.system() == "Darwin"
_TTS_IS_WIN = platform.system() == "Windows"
_TTS_IS_LINUX = platform.system() == "Linux"

# Optional: speak reasoning/explanations a bit slower for clarity in demos
SPEAK_EXPLANATIONS_SLOWER = True
SLOW_RATE_PYTTSX3 = 150   # default ~175 above; lower = slower
SLOW_RATE_MAC = "160"     # macOS 'say' expects a string; typical default ~175–200

def _init_pyttsx3():
    # This sets up the pyttsx3 text-to-speech engine, trying to pick a British English voice.
    global _TTS_ENGINE
    if pyttsx3 is None:
        return None
    engine = pyttsx3.init()
    # Look through available voices and pick one that sounds British.
    for v in engine.getProperty('voices'):
        if "en-gb" in v.id.lower() or "english_rp" in v.id.lower():
            engine.setProperty('voice', v.id)
            break
    engine.setProperty('rate', 175)  # Set speaking speed to a comfortable pace.
    return engine

def speak(text: str):
    """Speak text aloud in a British accent if possible."""
    # This function makes the bot talk out loud.
    # It chooses the right method depending on your computer.
    if not text.strip():
        return
    if _TTS_IS_MAC:
        _speak_mac(text)
    elif pyttsx3 is not None:
        _speak_pyttsx3(text)
    # If no speaking method is available, it just silently skips.

def _speak_mac(text: str):
    # On Mac computers, use the built-in 'say' command with a British voice named 'Daniel'.
    voice = 'Daniel'
    if not shutil.which('say'):
        return
    try:
        subprocess.run(['say', '-v', voice, text], check=False)
    except Exception:
        pass

def _speak_pyttsx3(text: str):
    # Use the pyttsx3 engine to speak text if available.
    global _TTS_ENGINE
    if _TTS_ENGINE is None:
        _TTS_ENGINE = _init_pyttsx3()
    if _TTS_ENGINE is None:
        return
    _TTS_ENGINE.say(text)
    _TTS_ENGINE.runAndWait()


# Speak on macOS with a given rate (as string)
def _speak_mac_with_rate(text: str, rate_str: str):
    voice = 'Daniel'
    if not shutil.which('say'):
        return
    try:
        subprocess.run(['say', '-v', voice, '-r', rate_str, text], check=False)
    except Exception:
        pass


def speak_slow(text: str):
    """Speak text a bit slower (for explanations). Falls back to normal speak()."""
    if not text or not text.strip():
        return
    if not SPEAK_EXPLANATIONS_SLOWER:
        speak(text)
        return
    if _TTS_IS_MAC:
        _speak_mac_with_rate(text, SLOW_RATE_MAC)
        return
    # pyttsx3 fallback: temporarily lower the rate
    if pyttsx3 is not None:
        global _TTS_ENGINE
        if _TTS_ENGINE is None:
            _TTS_ENGINE = _init_pyttsx3()
        if _TTS_ENGINE is None:
            return speak(text)
        try:
            current = _TTS_ENGINE.getProperty('rate')
            _TTS_ENGINE.setProperty('rate', SLOW_RATE_PYTTSX3)
            _TTS_ENGINE.say(text)
            _TTS_ENGINE.runAndWait()
            _TTS_ENGINE.setProperty('rate', current)
        except Exception:
            speak(text)
    else:
        speak(text)

# Helper: remove bracketed hints from spoken prompts (e.g., "(yes/no)")
# This cleans up prompts by removing things in parentheses so the speech sounds natural.
def strip_parentheticals(text: str) -> str:
    if not text:
        return ""
    try:
        # Remove any text within parentheses along with the parentheses themselves.
        cleaned = re.sub(r"\s*\([^)]*\)", "", text)
        # Make sure spacing looks nice.
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned
    except Exception:
        return text

# Knowledge base
# Words that might indicate someone is in crisis or thinking of self-harm.
CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "can't go on", "hopeless", "self-harm",
    "hurting myself", "overdose", "jump", "cut", "die", "ending it", "give up"
]

# Strategies the bot can suggest to help with different feelings or challenges.
STRATEGIES = {
    "mindfulness": {
        "desc": "Practice being present: try mindful breathing, or notice sensations around you.",
        "themes": ["anxiety", "stress", "overthinking", "panic"]
    },
    "journaling": {
        "desc": "Write down your thoughts and feelings for 5-10 minutes.",
        "themes": ["rumination", "sadness", "confusion"]
    },
    "reach out": {
        "desc": "Connect with a friend, family member, or helpline.",
        "themes": ["loneliness", "hopelessness", "crisis"]
    },
    "movement": {
        "desc": "Move your body gently—stretch, walk, or dance for a few minutes.",
        "themes": ["low energy", "tension", "restlessness"]
    },
    "self-compassion": {
        "desc": "Speak kindly to yourself as you would to a friend.",
        "themes": ["self-criticism", "shame", "guilt"]
    },
    "grounding": {
        "desc": "Try the 5-4-3-2-1 technique: notice 5 things you see, 4 you feel, 3 you hear, 2 you smell, 1 you taste.",
        "themes": ["panic", "dissociation", "anxiety"]
    }
}

# Utility helpers
def ask(prompt: str) -> str:
    # This function shows a question to the user and reads it aloud.
    # Then it waits for the user to type a response.
    print(textwrap.fill(prompt, width=80))
    speak(strip_parentheticals(prompt))
    return input("> ").strip()

def ask_choice(prompt: str, choices: t.List[str]) -> str:
    """Ask user to pick from choices (case-insensitive)."""
    # This helps the bot ask a question where the user must pick from given options.
    # It repeats the question until a valid choice is made.
    options = "/".join(choices)
    speak(strip_parentheticals(prompt))
    while True:
        answer = ask(f"{prompt} ({options})")
        for c in choices:
            if answer.lower() == c.lower():
                return c
        print("Please choose one of:", options)

def reflect_summary(user_inputs: t.List[str]) -> str:
    # Summarizes what the user has said so far, showing that the bot is listening.
    summary = "It sounds like: " + "; ".join(user_inputs)
    return summary

def contains_crisis(text: str) -> bool:
    # Checks if the user's response contains any words that might indicate a crisis.
    t_lower = text.lower()
    return any(kw in t_lower for kw in CRISIS_KEYWORDS)

def crisis_resources():
    # If a crisis is detected, this function shares helpful resources and encourages reaching out.
    msg = (
        "It sounds like you might be in a lot of pain. "
        "If you are thinking about harming yourself, please reach out for support. "
        "You can call the Suicide & Crisis Lifeline at 988 (in the US), or visit https://988lifeline.org/. "
        "You are not alone, always remember that."
    )
    print("\n" + textwrap.fill(msg, 80) + "\n")
    speak("If you’re in immediate danger, please call your local emergency number.")
    speak("Here are some resources you can reach out to right now.")

# Check-in questions and scoring
CHECKIN_QUESTIONS = [
    ("How are you feeling emotionally right now?", "emotion"),
    ("Are you experiencing any stress or anxiety? (none/mild/moderate/severe)", "stress"),
    ("How is your energy level? (low/ok/high)", "energy"),
    ("Are you having any thoughts that are hard to manage?", "thoughts"),
    ("Is there anything making things especially difficult today?", "difficulties"),
]

def score_checkin(answers: t.Dict[str, str]) -> int:
    """Simple scoring: higher means more distress."""
    # This function gives a score based on how serious the user's answers seem.
    # A higher score means the person might be struggling more.
    score = 0
    if "severe" in answers.get("stress", "").lower():
        score += 2
    elif "moderate" in answers.get("stress", "").lower():
        score += 1
    if "low" in answers.get("energy", "").lower():
        score += 1
    if any(kw in answers.get("thoughts", "").lower() for kw in CRISIS_KEYWORDS):
        score += 3
    if answers.get("difficulties", "").strip():
        score += 1
    return score

# Decision-tree follow-ups
def follow_up(answers: t.Dict[str, str]) -> t.List[str]:
    """Ask further questions based on check-in."""
    # Based on the user's answers, the bot asks more detailed questions to understand better.
    follow_ups = []
    if "severe" in answers.get("stress", "").lower():
        txt = "I'm sorry to hear your stress feels severe. Would you like to share more about what's causing it?"
        follow_ups.append(ask(txt))
    if "low" in answers.get("energy", "").lower():
        txt = "Low energy can be tough. Have you been able to rest or take care of yourself lately?"
        follow_ups.append(ask(txt))
    if answers.get("difficulties", "").strip():
        txt = "Thank you for sharing what's difficult. Is there any support you wish you had right now?"
        follow_ups.append(ask(txt))
    return follow_ups

# Recommendation functions
def rank_themes(answers: t.Dict[str, str]) -> t.List[str]:
    """Extract key themes from user answers."""
    # This looks at the user's responses to find common feelings or challenges (called themes).
    themes = []
    if "anx" in answers.get("stress", "").lower():
        themes.append("anxiety")
    if "low" in answers.get("energy", "").lower():
        themes.append("low energy")
    if "overthink" in answers.get("thoughts", "").lower():
        themes.append("overthinking")
    if "hopeless" in answers.get("emotion", "").lower():
        themes.append("hopelessness")
    if "panic" in answers.get("emotion", "").lower():
        themes.append("panic")
    if "lonely" in answers.get("emotion", "").lower():
        themes.append("loneliness")
    if "self-crit" in answers.get("thoughts", "").lower():
        themes.append("self-criticism")
    # Add more extraction as needed
    return themes

def choose_strategies(themes: t.List[str]) -> t.List[str]:
    """Pick strategies matching themes."""
    # Matches the themes found in the user's answers to helpful strategies from our list.
    recs = []
    for k, v in STRATEGIES.items():
        if any(t in v["themes"] for t in themes):
            recs.append(k)
    # If none matched, suggest general support
    if not recs:
        recs = ["mindfulness", "reach out"]
    return recs

def print_recommendations(strategies: t.List[str]):
    # Shows the user the suggested strategies and reads them out loud.
    print("\nHere are some things you might try to support yourself:\n")
    for k in strategies:
        s = STRATEGIES[k]
        print(f"- {k.title()}: {s['desc']}")
        speak(f"{k.title()}: {s['desc']}")
    print()

# Simple cues per theme: what we "heard" vs. what we might expect
THEME_CUES: t.Dict[str, t.Dict[str, t.List[str]]] = {
    # theme: {"present": [keywords], "missing_examples": [plain-language items]}
    "anxiety": {
        "present": ["anx", "worry", "on edge", "keyed-up", "keyed up", "panic"],
        "missing_examples": ["muscle tension", "racing thoughts", "restlessness"],
    },
    "low energy": {
        "present": ["low energy", "exhausted", "tired"],
        "missing_examples": ["refreshing sleep", "regular meals", "light activity"],
    },
    "overthinking": {
        "present": ["overthink", "ruminat"],
        "missing_examples": ["time-boxed worry", "journaling"],
    },
    "hopelessness": {
        "present": ["hopeless"],
        "missing_examples": ["recent positive moments", "supportive contact"],
    },
    "panic": {
        "present": ["panic"],
        "missing_examples": ["grounding technique used", "breathing exercise tried"],
    },
    "loneliness": {
        "present": ["lonely", "alone"],
        "missing_examples": ["recent check-in with someone"],
    },
    "self-criticism": {
        "present": ["self-crit", "guilt", "shame"],
        "missing_examples": ["self‑compassion practice"],
    },
}

def explain_why(strategies: t.List[str], themes: t.List[str], answers: t.Dict[str, str]):
    """Explain why strategies were suggested, and gently note what wasn't mentioned.

    We highlight which themes appeared in the user's text ("signals heard") and
    then name 1–2 simple items we didn't hear that would strengthen or refine
    guidance ("signals not heard"). This keeps the expert-system vibe without
    sounding robotic.
    """
    combined = (" ".join(answers.values())).lower()

    if themes:
        reason = f"I suggested these because you mentioned: {', '.join(themes)}."
        print(reason)
        speak_slow("Here is why I suggested those.")
    else:
        print("These are generally helpful strategies for well-being.")
        speak("These are generally helpful strategies for well-being.")
        return

    # Brief, readable per-theme evidence
    for theme in themes[:3]:  # cap to top 3 themes for brevity
        cues = THEME_CUES.get(theme, {"present": [], "missing_examples": []})
        heard = [k for k in cues.get("present", []) if k in combined]
        missing = [m for m in cues.get("missing_examples", []) if m.lower() not in combined]
        line = "  • " + theme.title() + ": "
        if heard:
            line += "signals heard → " + ", ".join(sorted(set(heard)))
        else:
            line += "signals heard → general check‑in responses"
        if missing:
            line += "; signals not heard → " + ", ".join(missing[:2])
        print(line)
        # Speak a simplified version of the line
        spoken_line = theme.title() + ". "
        if heard:
            spoken_line += "I noticed signals like " + ", ".join(sorted(set(heard))) + ". "
        else:
            spoken_line += "I mainly relied on your general responses. "
        if missing:
            spoken_line += "I did not hear mentions of " + ", ".join(missing[:2]) + "."
        speak_slow(spoken_line)
    print()

# Main conversational loop
# This is the heart of the bot. It guides the user through:
# 1. A friendly check-in with questions.
# 2. Detecting any crisis language and providing resources if needed.
# 3. Summarizing what the user shared.
# 4. Asking follow-up questions based on their responses.
# 5. Scoring their answers to understand their current state.
# 6. Suggesting personalized coping strategies.
# 7. Offering to guide the user through one of these strategies.
def run_bot():
    print("Hello, I'm here to support your mental wellness today.")
    speak("Hello, I'm here to support your mental wellness today.")
    print("Let's do a quick check-in. You can type as much or as little as you like.")
    speak("Let's do a quick check-in. You can type as much or as little as you like.")
    answers = {}
    crisis_flag = False
    user_inputs = []
    for q, key in CHECKIN_QUESTIONS:
        resp = ask(q)
        answers[key] = resp
        user_inputs.append(resp)
        if contains_crisis(resp):
            crisis_flag = True
    if crisis_flag:
        crisis_resources()
        return
    # Reflective summary
    summary = reflect_summary(user_inputs)
    print("\n" + summary)
    speak("Thanks for sharing. I’ll tailor suggestions based on that.")
    print("\nI’ll ask a couple of quick follow-up questions to tailor things.")
    speak("I’ll ask a couple of quick follow-up questions to tailor things.")
    # Follow-up questions
    followup_resps = follow_up(answers)
    if followup_resps:
        print("\nThank you for sharing more.")
        speak("Thank you for sharing more.")
    # Score and recommend
    score = score_checkin(answers)
    themes = rank_themes(answers)
    strategies = choose_strategies(themes)
    print("\nBased on what you shared, here are some personalized suggestions:")
    speak("Based on what you shared, here are some personalized suggestions.")
    print_recommendations(strategies)
    print("\nHere’s why I suggested those strategies:")
    speak_slow("Here’s why I suggested those strategies.")
    explain_why(strategies, themes, answers)
    # Crisis check again for follow-ups
    if any(contains_crisis(r) for r in followup_resps):
        crisis_resources()
        return
    # Offer to try an exercise
    print("\nIf you’d like, we can try one strategy together now.")
    speak("If you’d like, we can try one strategy together now.")
    choice = ask_choice(
        "Would you like to try one of these strategies now?", ["yes", "no"]
    )
    if choice.lower() == "yes":
        chosen = ask_choice(
            "Which would you like to try?", [k.title() for k in strategies]
        )
        chosen_key = chosen.lower()
        print(f"Great! Here are some steps for {chosen_key.title()}:")
        speak(f"Here are some steps for {chosen_key.title()}.")
        print(STRATEGIES[chosen_key]["desc"])
        speak(STRATEGIES[chosen_key]["desc"])
    print("\nBefore we wrap up, just a quick reminder:")
    speak("Before we wrap up, just a quick reminder.")
    print("\nThank you for checking in today. Remember, you're not alone.")
    speak("Thank you for checking in today. Remember, you're not alone.")
    print("If things feel hard, reaching out to a professional or a trusted person can help.")
    speak("If things feel hard, reaching out to a professional or a trusted person can help.")


# Entry point
if __name__ == "__main__":
    run_bot()