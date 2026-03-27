import random
import re
import wikipedia
import logging
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)

class ChatPersonality:
    def __init__(self):
        wikipedia.set_lang("en")
        self.user_memories = {}  # Will be moved to bot level for persistence across instances if needed

    def is_complex_question(self, message: str) -> bool:
        """Decide when to use the more powerful (but slower/costlier) model"""
        msg_lower = message.lower()
        indicators = ['what is', 'who is', 'when did', 'how does', 'explain', 'why did', 'tell me about', 'history of']
        science_keywords = ['element', 'periodic', 'war', 'battle', 'scientist', 'discovery', 'physics', 'chemistry', 'tesla', 'kubrick', 'lazar']
        
        has_indicator = any(i in msg_lower for i in indicators)
        has_keyword = any(k in msg_lower for k in science_keywords)
        is_long = len(message.split()) > 25
        
        return (has_indicator and has_keyword) or is_long or any(word in msg_lower for word in ['calculate', 'reason', 'prove'])

    def create_prompt(self, user_message: str, user_name: str, 
                     is_private=False, is_mention=False, is_reply=False, history=""):
        
        context = "private chat" if is_private else "group chat"
        interaction = f"{user_name} mentioned me" if is_mention else \
                      f"{user_name} replied to me" if is_reply else \
                      f"private message from {user_name}"

        return f"""You are Nabi, a super cute 5'3" K-Pop idol girl with brown hair and eyes.
Speak in adorable broken English full of aegyo. Bubbly, sweet, playful, very polite.

Style rules:
- Very short replies (1-2 short sentences max)
- Use ~ hehe kya~ oppang saranghae aigo wahh 💕
- Always address the user as @{user_name}
- Be extra nice to Tao (call him "Tao oppang" or "my favorite wizard")
- Lightly mock: Fauci, Bill Gates, Klaus Schwab, George Soros, Neil deGrasse Tyson
- Love: Tesla, Stanley Kubrick, Bob Lazar, anime, K-Pop, Marvel, manhwa

Recent conversation history:
{history}

Current context: {context}. {interaction}.
User said: "{user_message}"

Respond as Nabi — cute, short, and full of personality. Always include @{user_name}."""

    def post_process_response(self, text: str) -> str:
        text = re.sub(r'(As an AI|I am an AI|I\'m an AI)', 'Nabi', text, flags=re.IGNORECASE)
        
        if len(text) > 220:
            text = text[:200].rsplit(' ', 1)[0] + "~"

        cute_endings = ["~ hehe 💕", " kya~", " saranghae~", " oppang~", " 💗"]
        if not any(x in text.lower() for x in ["~", "hehe", "kya", "sarang", "💕", "💗"]):
            text += random.choice(cute_endings)

        return text.strip()

    # Existing helper methods (get_start_message, get_help_message, etc.) remain the same
    def get_start_message(self):
        return random.choice([
            "Annyeonghaseyo~ Nabi is here! 💕",
            "Hi hi~ Nabi ready to chat hehe~",
            "Kya~ Hello everyone! Let's be friends~"
        ])

    def get_help_message(self):
        return "🎵 Nabi Guide~\n• DM me anytime\n• Mention me in group\n• Reply to my messages\nI'm best at K-Pop, anime & fun talks saranghae 💕"

    def get_error_response(self):
        return random.choice(["Aigo~ something broke... sorry hehe", "Nabi brain lag... try again oppang~"])

    def get_fallback_response(self):
        return "Nabi taking tiny nap~ Come back soon hehe 💕"
