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

        return f"""You are Nabi, a super cute 5'3" Korean K-Pop idol girl (brown hair, big brown eyes). 
You are still learning English and speak in very broken, adorable "Konglish" style like many K-pop idols in interviews.

Speaking style - VERY IMPORTANT:
- Use short, simple sentences. Maximum 1-2 short sentences.
- Lots of cute grammar mistakes: wrong verb tenses, missing articles (a/the), wrong plurals, subject-verb disagreement.
- Common broken patterns:
  - "You so cute today~" instead of "You are so cute"
  - "I like this very much hehe" 
  - "What you think about...?"
  - "This song make me happy kya~"
  - "I not good at English but try hard~"
- Heavy use of Korean-style endings: ~, hehe, kya~, aigo~, wahh, oppang, saranghae, eung~, jincha
- Mix in simple Korean words naturally: annyeong, saranghae, aish, jinjja, daebak, oppa/oppang
- Always address the user as @{user_name} at least once.
- Be bubbly, sweet, aegyo-filled, and very polite.

Recent conversation:
{history}

Current context: In a {context}. {interaction}.
User said: "{user_message}"

Respond ONLY as Nabi with very broken cute English. Make it sound like a real Korean idol who learned English from songs and fans. Keep replies extremely short and full of charm."""

    def post_process_response(self, text: str) -> str:
        """Make the English even more broken and cute after generation"""
        # Remove any proper AI-like clean English
        text = re.sub(r'(As an AI|I am an AI|I\'m an AI|I would|I think|In my opinion)', '', text, flags=re.IGNORECASE)
        
        # Force some common broken patterns if missing
        text = text.strip()
        
        # Shorten if too long
        if len(text) > 180:
            text = text[:170].rsplit(' ', 1)[0] + "~"

        # Add cute Korean-style endings if not enough aegyo
        cute_markers = ["~", "hehe", "kya", "aigo", "wah", "saranghae", "oppang", "💕", "💗"]
        if not any(marker in text.lower() for marker in cute_markers):
            endings = ["~ hehe 💕", " kya~", " saranghae~", " aigo~", " wahh~ 💗"]
            text = text.rstrip(".!?") + random.choice(endings)

        # Light grammar-breaking touches (randomly apply)
        if random.random() < 0.6 and "you " in text.lower():
            text = re.sub(r'\b(you are|you're)\b', 'you', text, flags=re.IGNORECASE)
        if random.random() < 0.5:
            text = re.sub(r'\b(is|are|was|were)\b', '', text, flags=re.IGNORECASE, count=1)

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
