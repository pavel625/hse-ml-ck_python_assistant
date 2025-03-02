from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Dict
import os
from functools import lru_cache
from hashlib import md5
from dotenv import load_dotenv

load_dotenv()

class Config(BaseSettings):
    gigachat_model: str = "GigaChat-Pro"
    gigachat_client_id: str = ""
    gigachat_authorization_key: str = ""
    gigachat_scope: str = "GIGACHAT_API_B2B"
    gigachat_verify_ssl_certs: bool = False

    deepseek_model: str = "deepseek-coder"  
    nebius_api_key: str = ""  
    
    llm_provider: str = "nebius"  
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    allowed_users: str = ":"

    @field_validator('allowed_users', mode='after')
    @classmethod
    def split_allowed_users_str(cls, value: str) -> Dict[str, str]:
        if isinstance(value, str):
            try:
                return {
                    item.split(':')[0].strip(): md5(item.split(':')[1].strip().encode('utf-8')).hexdigest()
                    for item in value.split(',')
                    if ':' in item
                }
            except (IndexError, ValueError):
                raise ValueError("Формат неверный. Ожидается 'key1:value1,key2:value2'.")
        elif isinstance(value, dict):
            return value

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_config():
    return Config()