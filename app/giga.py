from langchain_gigachat import GigaChat
from langchain.schema import HumanMessage, SystemMessage
import logging
from typing import Optional
from config import get_config
import logging_config

logger = logging.getLogger(__name__)
config = get_config()

class GigaChatWrapper:
    def __init__(self, token: str, model_name: str = config.gigachat_model, system_prompt: str = None, 
                 temperature: float = 0.6, max_tokens: int = 2000):
        self.messages = []
        self.system_prompt = system_prompt
        self.giga = GigaChat(
            credentials=token,
            scope=config.gigachat_scope,
            model=model_name,
            verify_ssl_certs=config.gigachat_verify_ssl_certs
        )
        self.completion_options = {"temperature": temperature, "max_tokens": max_tokens}

    def ask(self, user_message: str, clear_history: bool = True):
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
            output = self.giga.invoke(langchain_messages, **self.completion_options)
            logger.info(f"ответ от GigaChat: {output.content}")
            return output.content
        except Exception as e:
            logger.error(f"Ошибка GigaChat: {str(e)}")
            return None