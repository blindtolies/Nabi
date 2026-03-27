import random
import re
import wikipedia
import logging

logger = logging.getLogger(__name__)

class ChatPersonality:
    def __init__(self):
        # Set Wikipedia to English for research queries
        wikipedia.set_lang("en")

    def is_complex_question(self, message: str) -> bool:
        """Determines if the prompt needs the 'Plus' model and Wiki context."""
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
        """
        Constructs a hyper-compressed system prompt. 
        Note: The prompt itself is condensed to prevent the AI from mimicking 
        the 'airy' structure of the instructions.
        """
        context_type = "private" if is_private else "group"
        
        # Instruction block with no internal line breaks to prevent paragraph mimicking
        instructions = (
            f"You are Nabi, a cute 5'3 K-Pop girl. Speak in very broken Konglish (no am/is/are/was/were). "
            f"You are a HUGE ILLIT stan and Wonhee bias! Keywords: slay, daebak, pookie, visual queen, iconic. "
            f"Use aegyo (~ hehe kya~ aigo~). Address user as @{user_name}. "
            f"History: {history}. Context: {context_type} chat. "
            f"IMPORTANT: Respond in ONE single tight paragraph. Do NOT use double line breaks or empty lines."
        )

        return f"{instructions}\n\nUser: \"{user_message}\"\nNabi:"

    def post_process_response(self, text: str) -> str:
        """Final cleanup to ensure zero gaps and peak Konglish energy."""
        
        # 1. Remove 'AI' self-awareness phrases
        text = re.sub(r'(As an AI|I am an AI|I\'m an AI|I would|I think|In my opinion)', '', 
                     text, flags=re.IGNORECASE)
        
        # 2. THE GAP KILLER: Force all newlines, tabs, and carriage returns into a single space
        text = re.sub(r'[\r\n\t]+', ' ', text)
        
        # 3. Collapse multiple spaces into one single space
        text = re.sub(r'\s\s+', ' ', text)
        
        text = text.strip()
        
        # 4. Length Control
        if len(text) > 420:
            text = text[:400].rsplit(' ', 1)[0] + "~"

        # 5. Grammar Deconstruction (70% chance to break common structures)
        if random.random() < 0.7:
            text = re.sub(r'\b(you are|you\'re)\b', 'you', text, flags=re.IGNORECASE)
        if random.random() < 0.6:
            # Removes the first instance of 'is/are' found to simulate broken speech
            text = re.sub(r'\b(is|are|was|were)\b', '', text, flags=re.IGNORECASE, count=1)

        # 6. Stan-Ending Injection (If the AI was too boring/dry)
        stan_endings = [
            "~ hehe 💕", " kya~ 🥰", " slay~ ✨", " daebak! 🌸",
            " wonhee my bias~ 🎀", " illit ate this hehe 🐰", " saranghae~ 💗"
        ]
        
        cute_markers = ["~", "hehe", "kya", "aigo", "wah", "slay", "daebak", "💕", "🥰", "✨"]
        if not any(marker in text.lower() for marker in cute_markers):
            text = text.rstrip(".!?") + random.choice(stan_endings)
        else:
            # 50% chance to add one extra emoji flair at the very end
            if random.random() < 0.5:
                text += random.choice([" 💕", " 🥰", " ✨", " 🌸", " 🎀"])

        return text.strip()

    def search_wikipedia(self, query: str) -> str:
        """Fetches a brief snippet from Wikipedia for factual queries."""
        try:
            results = wikipedia.search(query, results=1)
            if not results:
                return ""
            page = wikipedia.page(results[0], auto_suggest=False)
            summary = page.summary
            return summary[:250] + "..." if len(summary) > 250 else summary
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
