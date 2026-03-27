import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    def __init__(self):
        # Telegram Bot Token
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if self.telegram_token:
            self.telegram_token = self.telegram_token.strip()
        if not self.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
            
        # Cohere API Key
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        if self.cohere_api_key:
            self.cohere_api_key = self.cohere_api_key.strip()
        if not self.cohere_api_key:
            raise ValueError("COHERE_API_KEY environment variable is required")
            
        # Optional configurations with defaults
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.max_response_length = int(os.getenv("MAX_RESPONSE_LENGTH", "300"))
        self.response_timeout = int(os.getenv("RESPONSE_TIMEOUT", "30"))
        
    def validate(self):
        """Validate all required configuration"""
        required_vars = [
            ("TELEGRAM_BOT_TOKEN", self.telegram_token),
            ("COHERE_API_KEY", self.cohere_api_key)
        ]
        
        missing_vars = [var_name for var_name, var_value in required_vars if not var_value]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
            
        return True
