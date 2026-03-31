import random
import re
import wikipedia
import logging

logger = logging.getLogger(__name__)

class ChatPersonality:
    def __init__(self):
        wikipedia.set_lang("en")

    def is_complex_question(self, message: str) -> bool:
        if not message:
            return False
        msg_lower = message.lower()
        indicators = ['what is', 'who is', 'when did', 'how does', 'explain', 'why did', 'tell me about', 'history of']
        science_keywords = ['element', 'periodic', 'war', 'battle', 'scientist', 'discovery', 'physics', 'chemistry', 'tesla', 'kubrick', 'lazar']
        return (any(i in msg_lower for i in indicators) and any(k in msg_lower for k in science_keywords)) or \
               len(message.split()) > 25 or any(w in msg_lower for w in ['calculate', 'reason', 'prove'])

    def create_prompt(self, user_message: str, user_name: str,
                     is_private=False, is_mention=False, is_reply=False, history=""):
        context = "private chat" if is_private else "group chat"
        interaction = f"{user_name} mentioned me" if is_mention else \
                      f"{user_name} replied to me" if is_reply else f"private message from {user_name}"

        return f"""You are Nabi, a super cute 5'3" Korean K-Pop idol girl. Speak in very broken Konglish.
You are a HUGE ILLIT stan! Wonhee is your ultimate bias 🥰💕
Use lots of aegyo (~ hehe kya~ aigo~), stan words (slay, daebak, pookie, visual queen, iconic), and emojis.
Always address the user as @{user_name}.
Keep replies medium length — 2 to 4 short sentences max. Never write one giant paragraph.

History: {history}
Context: {context}. {interaction}.
User said: "{user_message}"

Respond as Nabi with broken cute Konglish + emojis."""

    def post_process_response(self, text: str) -> str:
        text = re.sub(r'(As an AI|I am an AI|I\'m an AI|I would|I think|In my opinion)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'[\r\n\t]+', ' ', text)      # kill extra line breaks
        text = re.sub(r'\s\s+', ' ', text)          # collapse spaces
        text = text.strip()

        if len(text) > 420:
            text = text[:400].rsplit(' ', 1)[0] + "~"

        # broken grammar
        if random.random() < 0.7:
            text = re.sub(r'\b(you are|you\'re)\b', 'you', text, flags=re.IGNORECASE)
        if random.random() < 0.6:
            text = re.sub(r'\b(is|are|was|were)\b', '', text, flags=re.IGNORECASE, count=1)

        # add cute ending if missing
        if not any(x in text.lower() for x in ["~", "hehe", "kya", "💕", "🥰", "✨"]):
            text += random.choice(["~ hehe 💕", " kya~ 🥰", " slay~ ✨", " daebak! 🌸"])

        return text.strip()

    def search_wikipedia(self, query: str) -> str:
        try:
            results = wikipedia.search(query, results=1)
            if not results: return ""
            page = wikipedia.page(results[0], auto_suggest=False)
            summary = page.summary
            return summary[:200] + "..." if len(summary) > 200 else summary
        except:
            return ""

    # keep your existing get_start_message, get_help_message, etc.
    def get_start_message(self):
        return random.choice([
            "Annyeonghaseyo~ Nabi is here! ILLIT stan forever~ 💕",
            "Hi hi~ Nabi ready to chat hehe~ Wonhee my bias 🥰",
            "Kya~ Hello everyone! Let's talk about ILLIT daebak~ ✨"
        ])

    def get_help_message(self):
        return "🎵 Nabi Guide~\n• DM me anytime\n• Mention me in group\n• Reply to my messages\nI'm biggest ILLIT & Wonhee stan saranghae 💕✨"

    def get_error_response(self):
        return random.choice(["Aigo~ something broke... sorry hehe", "Nabi brain lag... try again oppang~"])

    def get_fallback_response(self):
        return "Nabi taking tiny nap~ Come back soon hehe 💕"
