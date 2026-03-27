import logging
import asyncio
import random
from collections import deque, defaultdict
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.ext import AIORateLimiter   # New

import cohere

from personality import ChatPersonality
from config import Config

logger = logging.getLogger(__name__)

class ChatBot:
    def __init__(self):
        self.config = Config()
        self.personality = ChatPersonality()
        self.cohere_client = cohere.ClientV2(self.config.cohere_api_key)
        self.bot_username = "@Nabi_Chat_Bot".lower()

        # Conversation memory: user_id -> deque of (role, content)
        self.conversations = defaultdict(lambda: deque(maxlen=8))  # Keep last 8 turns

        self.application = None

    async def start(self):
        token = self.config.telegram_token
        if not token:
            raise ValueError("Telegram token is required")

        # Enable built-in rate limiter (prevents Telegram flood limits)
        rate_limiter = AIORateLimiter(
            overall_max_rate=30,      # max 30 messages per second globally
            overall_time_period=1,
            group_max_rate=20,        # per group/chat
            group_time_period=60
        )

        self.application = (
            Application.builder()
            .token(token)
            .rate_limiter(rate_limiter)   # Important
            .build()
        )

        # Handlers (order matters)
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

        logger.info("🚀 Nabi Bot starting with memory + rate limiting + smart model switching...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

        logger.info("✅ Nabi is online and cuter than ever~ 💕")
        await asyncio.Event().wait()

    # Command handlers (unchanged except logging)
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message:
            await update.message.reply_text(self.personality.get_start_message())

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message:
            await update.message.reply_text(self.personality.get_help_message())

    # Unified processing with memory
    async def _process_message(self, update: Update, is_private=False, is_mention=False, is_reply=False):
        if not update.message or not update.message.text:
            return

        user_message = update.message.text.strip()
        user = update.effective_user
        user_name = user.username or user.first_name or "friend"
        user_id = user.id

        # Add user message to memory
        self.conversations[user_id].append(("user", user_message))

        try:
            # Build short history string
            history = "\n".join([f"{role}: {content}" for role, content in list(self.conversations[user_id])[:-1]])

            response = await self.generate_response(
                user_message, user_name, history,
                is_private=is_private, is_mention=is_mention, is_reply=is_reply
            )

            await update.message.reply_text(response)

            # Add bot response to memory
            self.conversations[user_id].append(("assistant", response))

        except Exception as e:
            logger.error(f"Error processing message from {user_name}: {e}")
            fallback = self.personality.get_error_response()
            await update.message.reply_text(fallback)

    # Handlers call the unified processor
    async def handle_private_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._process_message(update, is_private=True)

    async def handle_mention(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._process_message(update, is_mention=True)

    async def handle_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.reply_to_message and update.message.reply_to_message.from_user.is_bot:
            await self._process_message(update, is_reply=True)

    async def handle_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text:
            return

        text_lower = update.message.text.lower()
        if self.bot_username in text_lower or \
           (update.message.reply_to_message and update.message.reply_to_message.from_user.is_bot):
            return

        trigger_keywords = ['anime', 'kpop', 'cat', 'marvel', 'manhwa', 'tao', 'based', 'kino',
                            'tesla', 'kubrick', 'fauci', 'gates', 'schwab']
        has_trigger = any(kw in text_lower for kw in trigger_keywords)

        chance = 0.09 if has_trigger else 0.012   # Slightly tuned

        if random.random() < chance:
            await self._process_message(update, is_private=False)

    async def generate_response(self, user_message: str, user_name: str, history: str,
                               is_private=False, is_mention=False, is_reply=False):
        try:
            # Smart model selection
            use_plus = self.personality.is_complex_question(user_message)
            model = "command-r-plus-08-2024" if use_plus else "command-r-08-2024"

            wiki_info = ""
            if self.personality.is_complex_question(user_message):  # Reuse the same check
                try:
                    wiki_result = self.personality.search_wikipedia(user_message)  # You can keep the method from before
                    if wiki_result and len(wiki_result) > 10:
                        wiki_info = f"\n\nContext: {wiki_result[:300]}"
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
                max_tokens=140,
                temperature=0.92,
                p=0.95,
            )

            generated = response.message.content[0].text.strip()
            return self.personality.post_process_response(generated)

        except Exception as e:
            logger.error(f"Cohere error ({model}): {e}")
            return self.personality.get_fallback_response()
