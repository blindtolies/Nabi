import logging
import asyncio
import cohere
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from personality import ChatPersonality
from config import Config

logger = logging.getLogger(__name__)

class ChatBot:
    def __init__(self):
        self.config = Config()
        self.personality = ChatPersonality()
        self.cohere_client = cohere.ClientV2(self.config.cohere_api_key)
        self.application = None
        self.bot_username = "@Chat_Chat_Bot"
        
    async def start(self):
        """Initialize and start the bot"""
        try:
            # Create application - telegram_token is guaranteed to be a string by config validation
            token = self.config.telegram_token
            if not token:
                raise ValueError("Telegram token is required")
            self.application = Application.builder().token(token).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            
            # Message handlers - order matters!
            self.application.add_handler(MessageHandler(
                filters.TEXT & filters.REPLY, 
                self.handle_reply
            ))
            self.application.add_handler(MessageHandler(
                filters.TEXT & filters.Entity("mention"), 
                self.handle_mention
            ))
            self.application.add_handler(MessageHandler(
                filters.TEXT & filters.ChatType.PRIVATE, 
                self.handle_private_message
            ))
            # NEW: Handle all group messages (with random chance to respond)
            self.application.add_handler(MessageHandler(
                filters.TEXT & filters.ChatType.GROUPS,
                self.handle_group_message
            ))
            
            # Start the bot
            logger.info("Starting Harley Quinn Bot...")
            await self.application.initialize()
            await self.application.start()
            if self.application.updater:
                await self.application.updater.start_polling()
            
            # Keep the bot running
            logger.info("Bot is running! Press Ctrl+C to stop.")
            await asyncio.Event().wait()
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
        finally:
            if self.application:
                await self.application.stop()
                
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        if not update.message:
            return
        response = self.personality.get_start_message()
        await update.message.reply_text(response)
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        if not update.message:
            return
        response = self.personality.get_help_message()
        await update.message.reply_text(response)
        
    async def handle_private_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle private messages"""
        if not update.message or not update.message.text:
            return
            
        user_message = update.message.text
        user_name = update.effective_user.username or update.effective_user.first_name or "stranger" if update.effective_user else "stranger"
        
        try:
            response = await self.generate_response(user_message, user_name, is_private=True)
            await update.message.reply_text(response)
        except Exception as e:
            logger.error(f"Error handling private message: {e}")
            fallback_response = self.personality.get_error_response()
            await update.message.reply_text(fallback_response)
            
    async def handle_mention(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages that mention the bot"""
        if not update.message or not update.message.text:
            return
            
        user_message = update.message.text
        user_name = update.effective_user.username or update.effective_user.first_name or "stranger" if update.effective_user else "stranger"
        
        # Check if the bot is mentioned
        if self.bot_username.lower() in user_message.lower():
            try:
                response = await self.generate_response(user_message, user_name, is_mention=True)
                await update.message.reply_text(response)
            except Exception as e:
                logger.error(f"Error handling mention: {e}")
                fallback_response = self.personality.get_error_response()
                await update.message.reply_text(fallback_response)
                
    async def handle_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle replies to bot messages"""
        if not update.message or not update.message.text:
            return
            
        # Check if the reply is to a bot message
        if (update.message.reply_to_message and 
            update.message.reply_to_message.from_user and 
            update.message.reply_to_message.from_user.is_bot):
            
            user_message = update.message.text
            user_name = update.effective_user.username or update.effective_user.first_name or "stranger" if update.effective_user else "stranger"
            
            try:
                response = await self.generate_response(user_message, user_name, is_reply=True)
                await update.message.reply_text(response)
            except Exception as e:
                logger.error(f"Error handling reply: {e}")
                fallback_response = self.personality.get_error_response()
                await update.message.reply_text(fallback_response)

    async def handle_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle random interjections in group chats - HYBRID MODE"""
        if not update.message or not update.message.text:
            return
        
        # Skip if already handled by mention/reply handlers
        user_message = update.message.text
        if self.bot_username.lower() in user_message.lower():
            return
        if update.message.reply_to_message and update.message.reply_to_message.from_user and update.message.reply_to_message.from_user.is_bot:
            return
            
        # HYBRID APPROACH: Higher chance with keywords, low baseline chance
        
        # Define trigger keywords based on Chat's interests
        trigger_keywords = [
            # Topics she knows/loves
            'anime', 'cat',
            'marvel', 'manhwa', 'comic', 'kpop',
            # Things she mocks
            'liberal',
            # Conspiracy theories
            'mandela effect', 'aliens',
            # Her relationships
            'tao',
            # Other personality traits
            'based', 'kino',
        ]
        
        # Check if any trigger keyword is in the message
        message_lower = user_message.lower()
        has_trigger = any(keyword in message_lower for keyword in trigger_keywords)
        
        # Determine response chance
        if has_trigger:
            response_chance = 0.02  # 2% chance when keywords present
        else:
            response_chance = 0.02  # 2% baseline chance for random sass
        
        # Roll the dice
        if random.random() < response_chance:
            user_name = update.effective_user.username or update.effective_user.first_name or "stranger" if update.effective_user else "stranger"
            try:
                response = await self.generate_response(user_message, user_name, is_private=False)
                await update.message.reply_text(response)
            except Exception as e:
                logger.error(f"Error handling group message: {e}")
                
    def is_science_history_question(self, message: str) -> bool:
        """Check if the message is asking for science or history information"""
        question_indicators = ['what is', 'who is', 'when did', 'where is', 'how did', 'why did', 'tell me about', 'explain']
        science_history_keywords = ['element', 'periodic', 'history', 'war', 'battle', 'emperor', 'king', 'queen', 'century', 'year', 'chemical', 'physics', 'biology', 'planet', 'scientist', 'discovery', 'invention']
        
        message_lower = message.lower()
        has_question = any(indicator in message_lower for indicator in question_indicators)
        has_topic = any(keyword in message_lower for keyword in science_history_keywords)
        
        # Also check for periodic table format with #
        has_periodic_table_format = '#' in message and any(char.isdigit() for char in message)
        
        return (has_question and has_topic) or has_periodic_table_format

    async def generate_response(self, user_message: str, user_name: str, is_private=False, is_mention=False, is_reply=False):
        """Generate AI response using Cohere Chat API"""
        try:
            # Check if this is a science/history question
            wiki_info = ""
            if self.is_science_history_question(user_message):
                wiki_result = self.personality.search_wikipedia(user_message)
                if wiki_result and "Wikipedia failed" not in wiki_result and "Couldn't find" not in wiki_result:
                    wiki_info = f"\n\nWikipedia info: {wiki_result}"
            
            # Create context-aware prompt
            system_prompt = self.personality.create_prompt(
                user_message + wiki_info, 
                user_name, 
                is_private=is_private, 
                is_mention=is_mention, 
                is_reply=is_reply
            )
            
            # Generate response with Cohere Chat API
            response = self.cohere_client.chat(
                model='command-r-08-2024',
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_message + wiki_info
                    }
                ],
                max_tokens=180,
                temperature=1.00,
            )
            
            generated_text = response.message.content[0].text.strip()
            
            # Post-process the response to ensure it fits Harley's personality
            final_response = self.personality.post_process_response(generated_text)
            
            return final_response
            
        except Exception as e:
            logger.error(f"Error generating response with Cohere: {e}")
            return self.personality.get_fallback_response()
