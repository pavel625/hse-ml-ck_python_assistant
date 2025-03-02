from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import logging
from typing import Optional
from config import get_config
from prompts import deepseek_few_shot_v1
import logging_config

logger = logging.getLogger(__name__)
config = get_config()

class DeepSeekWrapper:
    def __init__(self, token: str, model_name: str = config.deepseek_model, 
                 temperature: float = 0.6, max_tokens: int = 2000):
        self.messages = []
        self.system_prompt = deepseek_few_shot_v1()
        self.deepseek = ChatOpenAI(
            openai_api_key=token,
            model_name=model_name,
            base_url="https://api.studio.nebius.ai/v1/",
        )
        self.completion_options = {"temperature": temperature, "max_tokens": max_tokens}

    async def ask(self, user_message: str, clear_history: bool = True):
        if clear_history:
            self.messages = []
            if self.system_prompt:
                self.messages.append({"role": "system", "text": self.system_prompt})
        self.messages.append({"role": "user", "text": user_message})
        
        langchain_messages = [
            SystemMessage(content=msg["text"]) if msg["role"] == "system" else HumanMessage(content=msg["text"])
            for msg in self.messages
        ]
        
        try:
            output = await self.deepseek.ainvoke(langchain_messages, **self.completion_options)
            logger.info(f"ответ от DeepSeek: {output.content}")
            return output.content
        except Exception as e:
            logger.error(f"Ошибка DeepSeek: {str(e)}", exc_info=True)
            return None