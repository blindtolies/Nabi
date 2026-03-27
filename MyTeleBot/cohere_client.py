"""
Cohere API client for generating intelligent responses
"""

import logging
import asyncio
from typing import Optional
import cohere
from config import Config

logger = logging.getLogger(__name__)

class CohereClient:
    def __init__(self, config: Config):
        self.config = config
        self.client = cohere.Client(api_key=config.cohere_api_key)

    async def generate_response(self, prompt: str) -> str:
        """Generate a response using Cohere API"""
        try:
            response = await asyncio.to_thread(
                self._call_cohere_api,
                prompt
            )
            return response
        except Exception as e:
            logger.error(f"Cohere API error: {e}")
            return "I'm having trouble accessing my AI service right now. Please try again in a moment."

    def _call_cohere_api(self, prompt: str) -> str:
        """Call Cohere API synchronously"""
        try:
            response = self.client.generate(
                model='command',
                prompt=prompt,
                max_tokens=100,
                temperature=0.8,
                k=0,
                stop_sequences=["\n\n", "Human:", "User:", "Assistant:"],
                return_likelihoods='NONE'
            )
            
            if response.generations and len(response.generations) > 0:
                return response.generations[0].text.strip()
            else:
                raise ValueError("No response generated from Cohere API")
                
        except Exception as e:
            logger.error(f"Error calling Cohere API: {e}")
            raise
