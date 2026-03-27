import random
import re
import wikipedia
import logging

logger = logging.getLogger(__name__)

class ChatPersonality:
    def __init__(self):
        wikipedia.set_lang("en")

    def is_complex_question(self, message: str) -> bool:
        """Decide when to use the more powerful model (command-r-plus)"""
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
        """Create strong broken Konglish prompt for Nabi"""
        context = "private chat" if is_private else "group chat"
        interaction = f"{user_name} mentioned me" if is_mention else \
                      f"{user_name} replied to me" if is_reply else \
                      f"private message from {user_name}"

        return f"""You are Nabi, a super cute 5'3" Korean K-Pop idol girl (brown hair, big brown eyes).
You are still learning English and speak in very broken, adorable "Konglish" style like many K-pop idols.

Speaking style - VERY IMPORTANT:
- Use very short sentences. Maximum 1-2 short sentences only.
- Lots of cute grammar mistakes: wrong verb tenses, missing "a/the", wrong plurals.
- Common broken patterns:
  - "You so cute today~"
  - "I like this very much hehe"
  - "What you think about...?"
  - "This song make me happy kya~"
  - "I not good at English but try hard~"
- Heavy aegyo: ~, hehe, kya~, aigo~, wahh, oppang, saranghae, jinjja, daebak
- Mix simple Korean words: annyeong, saranghae, aish, jinjja, daebak, oppa/oppang
- Always address the user as @{user_name} at least once.
- Be bubbly, sweet, playful, and very polite.

Recent conversation:
{history}

Current context: In a {context}. {interaction}.
User said: "{user_message}"

Respond ONLY as Nabi with very broken cute English. 
Make it sound like a real Korean idol who learned English from songs and fans. 
Keep replies extremely short and full of charm."""

    def post_process_response(self, text: str) -> str:
        """Make English even more broken and cute"""
        # Remove any clean/AI-like language
        text = re.sub(r'(As an AI|I am an AI|I\'m an AI|I would|I think|In my opinion)', '', 
                     text, flags=re.IGNORECASE)
        
        text = text.strip()
        
        # Shorten if too long
        if len(text) > 180:
            text = text[:170].rsplit(' ', 1)[0] + "~"

        # Add cute endings if missing aegyo
        cute_markers = ["~", "hehe", "kya", "aigo", "wah", "saranghae", "oppang", "💕", "💗"]
        if not any(marker in text.lower() for marker in cute_markers):
            endings = ["~ hehe 💕", " kya~", " saranghae~", " aigo~", " wahh~ 💗"]
            text = text.rstrip(".!?") + random.choice(endings)

        # Extra grammar breaking
        if random.random() < 0.65 and "you " in text.lower():
            text = re.sub(r'\b(you are|you're)\b', 'you', text, flags=re.IGNORECASE)
        if random.random() < 0.55:
            text = re.sub(r'\b(is|are|was|were)\b', '', text, flags=re.IGNORECASE, count=1)

        return text.strip()

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

    def search_wikipedia(self, query: str) -> str:
        """Simple Wikipedia search for complex questions"""
        try:
            results = wikipedia.search(query, results=1)
            if not results:
                return ""
            page = wikipedia.page(results[0], auto_suggest=False)
            summary = page.summary
            return summary[:280] + "..." if len(summary) > 280 else summary
        except Exception:
            return ""
