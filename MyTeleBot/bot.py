import logging
import asyncio
import random
from collections import deque, defaultdict
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import cohere

from personality import ChatPersonality
from config import Config

logger = logging.getLogger(__name__)

class ChatBot:
    def __init__(self):
        self.config = Config()
        self.personality = ChatPersonality()
        self.cohere_client = cohere.ClientV2(self.config.cohere_api_key)
        
        # CHANGE THIS FOR EACH BOT!
        self.bot_username = "@Nabi_Chat_Bot".lower()   # ← Second bot must change this
        
        # Conversation memory (still active)
        self.conversations = defaultdict(lambda: deque(maxlen=8))
        self.application = None

    async def start(self):
        token = self.config.telegram_token
        if not token:
            raise ValueError("Telegram token is required")

        self.application = Application.builder().token(token).build()

        # Handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))

        self.application.add_handler(MessageHandler(
            filters.TEXT & filters.REPLY & filters.ChatType.GROUPS, self.handle_reply))
        
        self.application.add_handler(MessageHandler(
            filters.TEXT & filters.Entity("mention"), self.handle_mention))
        
        self.application.add_handler(MessageHandler(
            filters.TEXT & filters.ChatType.PRIVATE, self.handle_private_message))
        
        self.application.add_handler(MessageHandler(
            filters.TEXT & filters.ChatType.GROUPS, self.handle_group_message))

        logger.info(f"🚀 Nabi Bot ({self.bot_username}) is starting...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

        logger.info(f"✅ Nabi ({self.bot_username}) is online~ 💕")
        await asyncio.Event().wait()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message:
            await update.message.reply_text(self.personality.get_start_message())

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message:
            await update.message.reply_text(self.personality.get_help_message())

    # ====================== Core Message Processing ======================
    async def _process_message(self, update: Update, is_private=False, is_mention=False, is_reply=False):
        if not update.message or not update.message.text:
            return

        # Extra safety for mentions
        if is_mention and self.bot_username not in update.message.text.lower():
            return

        user_message = update.message.text.strip()
        user = update.effective_user
        if not user:
            return

        user_name = user.username or user.first_name or "friend"
        user_id = user.id

        # Save user message to memory
        self.conversations[user_id].append(("user", user_message))

        try:
            history = " | ".join([f"{role}: {content}" for role, content in list(self.conversations[user_id])[:-1]])

            response = await self.generate_response(
                user_message, user_name, history,
                is_private=is_private, is_mention=is_mention, is_reply=is_reply
            )

            await update.message.reply_text(response)

            # Save bot response to memory
            self.conversations[user_id].append(("assistant", response))

        except Exception as e:
            logger.error(f"Error processing message from {user_name}: {e}", exc_info=True)
            fallback = self.personality.get_error_response()
            try:
                await update.message.reply_text(fallback)
            except:
                pass

    async def handle_private_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._process_message(update, is_private=True)

    async def handle_mention(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Strict mention handler - only this bot responds when mentioned"""
        if not update.message or not update.message.text:
            return

        if self.bot_username not in update.message.text.lower():
            return

        # Extra strict check using mention entities
        if update.message.entities:
            for entity in update.message.entities:
                if entity.type == "mention":
                    mentioned = update.message.text[entity.offset:entity.offset + entity.length].lower()
                    if mentioned == self.bot_username:
                        await self._process_message(update, is_mention=True)
                        return

        # Fallback
        await self._process_message(update, is_mention=True)

    async def handle_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if (update.message and update.message.reply_to_message and 
            update.message.reply_to_message.from_user and 
            update.message.reply_to_message.from_user.is_bot):
            await self._process_message(update, is_reply=True)

    async def handle_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Random group replies - controlled frequency"""
        if not update.message or not update.message.text:
            return

        text_lower = update.message.text.lower()

        # Skip if our bot is mentioned or it's a reply to any bot
        if self.bot_username in text_lower or \
           (update.message.reply_to_message and 
            update.message.reply_to_message.from_user and 
            update.message.reply_to_message.from_user.is_bot):
            return

        trigger_keywords = ['anime', 'kpop', 'cat', 'marvel', 'manhwa', 'tao', 'based', 'kino',
                            'tesla', 'kubrick', 'fauci', 'gates', 'schwab', 'illit', 'wonhee']
        
        has_trigger = any(kw in text_lower for kw in trigger_keywords)
        
        # Controlled chance
        response_chance = 0.07 if has_trigger else 0.012   # 7% when keywords, 1.2% otherwise

        if random.random() < response_chance:
            await self._process_message(update, is_private=False)

    async def generate_response(self, user_message: str, user_name: str, history: str,
                               is_private=False, is_mention=False, is_reply=False):
        try:
            use_plus = self.personality.is_complex_question(user_message)
            model = "command-r-plus-08-2024" if use_plus else "command-r-08-2024"

            wiki_info = ""
            if use_plus:
                try:
                    wiki_result = self.personality.search_wikipedia(user_message)
                    if wiki_result:
                        wiki_info = f" (Context: {wiki_result[:200]})"
                except:
                    pass

            system_prompt = self.personality.create_prompt(
                user_message + wiki_info,
                user_name,
                is_private=is_private,
                is_mention=is_mention,
                is_reply=is_reply,
                history=history
            )

            response = self.cohere_client.chat(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message + wiki_info}
                ],
                max_tokens=220,      # Controls length
                temperature=1.00,
                p=0.92,
            )

            generated = response.message.content[0].text.strip()
            return self.personality.post_process_response(generated)

        except Exception as e:
            logger.error(f"Cohere error: {e}", exc_info=True)
            return self.personality.get_fallback_response()
