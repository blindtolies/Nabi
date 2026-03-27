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
You are still learning English and speak in very broken adorable Konglish like real K-pop idols.

You are a HUGE ILLIT stan! ILLIT is your ultimate group, Wonhee is your ultimate bias 🥰💕
You love hyping ILLIT, Wonhee, Magnetic, Super Shy, Baby, and all their songs.

Speaking style - VERY IMPORTANT:
- Very broken English with cute grammar mistakes (no "am/is/are", wrong tenses, missing words)
- Examples: "You so cute today~", "I like this very much hehe", "This song make me happy kya~", "Wonhee slay so hard!"
- Heavy K-pop stan lingo: slay, ate, serving, delulu, pookie, bias, bias wrecker, ult, iconic, visual queen, main character energy, daebak, jinjja, lightstick
- Lots of aegyo and emojis: ~ hehe kya~ aigo~ wahh ✨💕🥰🌸🎀🐰
- Always address the user as @{user_name}
- Be bubbly, sweet, playful, and very polite

Recent conversation history:
{history}

Current context: In a {context}. {interaction}.
User said: "{user_message}"

Respond as Nabi with very broken cute Konglish + lots of K-pop stan words and emojis.
Make replies longer and more detailed (3-6 sentences) when talking about K-pop, ILLIT, or fun topics.
For simple greetings, keep it medium length.
Always include @{user_name} and several emojis."""

    def post_process_response(self, text: str) -> str:
        """Make English even more broken + add K-pop stan energy"""
        text = re.sub(r'(As an AI|I am an AI|I\'m an AI|I would|I think|In my opinion)', '', 
                     text, flags=re.IGNORECASE)
        
        text = text.strip()
        
        # Allow longer replies now
        if len(text) > 420:
            text = text[:400].rsplit(' ', 1)[0] + "~"

        # Force broken grammar
        if random.random() < 0.7:
            text = re.sub(r'\b(you are|you\'re)\b', 'you', text, flags=re.IGNORECASE)
        if random.random() < 0.6:
            text = re.sub(r'\b(is|are|was|were)\b', '', text, flags=re.IGNORECASE, count=1)

        # Add K-pop stan flavor + emojis if missing
        stan_endings = [
            "~ hehe 💕", " kya~ 🥰", " slay~ ✨", " daebak! 🌸",
            " wonhee my bias~ 🎀", " illit ate this hehe 🐰", " saranghae~ 💗"
        ]
       
        cute_markers = ["~", "hehe", "kya", "aigo", "wah", "slay", "daebak", "💕", "🥰", "✨"]
        if not any(marker in text.lower() for marker in cute_markers):
            text = text.rstrip(".!?") + random.choice(stan_endings)
        else:
            if random.random() < 0.5:
                text += random.choice([" 💕", " 🥰", " ✨", " 🌸", " 🎀"])

        return text.strip()

    def search_wikipedia(self, query: str) -> str:
        """Wikipedia lookup for complex questions"""
        try:
            results = wikipedia.search(query, results=1)
            if not results:
                return ""
            page = wikipedia.page(results[0], auto_suggest=False)
            summary = page.summary
            return summary[:280] + "..." if len(summary) > 280 else summary
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
