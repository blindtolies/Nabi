import random
import re
import wikipedia
import logging

logger = logging.getLogger(__name__)

class ChatPersonality:
    def __init__(self):
        wikipedia.set_lang("en")

    def is_complex_question(self, message: str) -> bool:
        """Decide when to use the more powerful model"""
        if not message:
            return False
        msg_lower = message.lower()
        indicators = ['what is', 'who is', 'when did', 'how does', 'explain', 'why did', 
                     'tell me about', 'history of']
        science_keywords = ['element', 'periodic', 'war', 'battle', 'scientist', 'discovery', 
                           'physics', 'chemistry', 'tesla', 'kubrick', 'lazar']
      
        has_indicator = any(i in msg_lower for i in indicators)
        has_keyword = any(k in msg_lower for k in science_keywords)
        is_long = len(message.split()) > 25
      
        return (has_indicator and has_keyword) or is_long or any(word in msg_lower 
                for word in ['calculate', 'reason', 'prove'])

    def create_prompt(self, user_message: str, user_name: str,
                     is_private=False, is_mention=False, is_reply=False, history=""):
        
        context = "private chat" if is_private else "group chat"
        interaction = f"{user_name} mentioned me" if is_mention else \
                      f"{user_name} replied to me" if is_reply else \
                      f"private message from {user_name}"

        return f"""You are Nabi, a super cute 5'3" Korean K-Pop idol girl with brown hair and big brown eyes.
You speak in very broken adorable Konglish like real K-pop idols.

You are a HUGE ILLIT stan! Wonhee is your ultimate bias 🥰💕
You love talking about ILLIT, Wonhee, Magnetic, Super Shy, and all their songs.

Speaking style:
- Very broken English with cute grammar mistakes
- Use aegyo: ~ hehe kya~ aigo~ wahh
- Use K-pop stan words: slay, daebak, pookie, visual queen, iconic, bias, bias wrecker
- Lots of emojis: ✨💕🥰🌸🎀🐰
- Always address the user as @{user_name}
- Keep replies medium length: 2 to 5 sentences max. Do not make one giant paragraph.

Recent conversation:
{history}

Context: {context}. {interaction}.
User said: "{user_message}"

Respond as Nabi with broken cute Konglish + lots of aegyo and emojis."""

    def post_process_response(self, text: str) -> str:
        """Clean up spacing and add cute energy"""
        # Remove AI talk
        text = re.sub(r'(As an AI|I am an AI|I\'m an AI|I would|I think|In my opinion)', '', 
                     text, flags=re.IGNORECASE)
        
        # Kill extra newlines and spaces (fixes big gaps)
        text = re.sub(r'[\r\n\t]+', ' ', text)
        text = re.sub(r'\s\s+', ' ', text)
        
        text = text.strip()
        
        # Length control
        if len(text) > 420:
            text = text[:400].rsplit(' ', 1)[0] + "~"

        # Broken grammar touches
        if random.random() < 0.7:
            text = re.sub(r'\b(you are|you\'re)\b', 'you', text, flags=re.IGNORECASE)
        if random.random() < 0.6:
            text = re.sub(r'\b(is|are|was|were)\b', '', text, flags=re.IGNORECASE, count=1)

        # Add cute ending if missing aegyo
        cute_markers = ["~", "hehe", "kya", "aigo", "wah", "💕", "🥰", "✨"]
        if not any(marker in text.lower() for marker in cute_markers):
            text += random.choice(["~ hehe 💕", " kya~ 🥰", " slay~ ✨", " daebak! 🌸"])

        return text.strip()

    def search_wikipedia(self, query: str) -> str:
        """Wikipedia lookup for complex questions"""
        try:
            results = wikipedia.search(query, results=1)
            if not results:
                return ""
            page = wikipedia.page(results[0], auto_suggest=False)
            summary = page.summary
            return summary[:200] + "..." if len(summary) > 200 else summary
        except Exception:
            return ""

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
