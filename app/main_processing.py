import os
import time
from typing import Optional, Tuple
import logging
from pydantic import BaseModel
import asyncio

from config import get_config
from giga import GigaChatWrapper
from deepseek import DeepSeekWrapper
from syntax_checker import SyntaxChecker
from prompts import gigachat_few_shot_v1
import logging_config
from schemas import ResponseData, MultiResponseData

logger = logging.getLogger(__name__)

config = get_config()

system_prompt = gigachat_few_shot_v1()

deepseek_llm = DeepSeekWrapper(
    token=config.nebius_api_key,  
    model_name=config.deepseek_model,
    temperature=0.29,
    max_tokens=40,
)
gigachat_llm = GigaChatWrapper(
    token=config.gigachat_authorization_key,
    model_name=config.gigachat_model,
    system_prompt=system_prompt,
    temperature=0.29,
    max_tokens=40,
)

syntax_checker = SyntaxChecker()

class ResponseData(BaseModel):
    id: str = ''
    short_hint: str = ''
    long_hint: str = ''
    model_used: str = ''

class MultiResponseData(BaseModel):
    id: str = ''
    short_hint: str = ''
    long_hint: str = ''
    model_used: str = ''

class DatasetRow:
    def __init__(self, data):
        self.task_condition = data.get("task_condition", "")
        self.student_solution = data.get("student_solution", "")
        self.checker_status = data.get("checker_status", "")
        self.stacktrace = data.get("stacktrace", "")
        self.proper_solution = data.get("proper_solution", "")
        self.id = data.get("id", "")

async def ask_with_timeout(llm, message, timeout=12):
    try:
        return await asyncio.wait_for(llm.ask(message, clear_history=True), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"Таймаут {timeout} секунд превышен для {llm.__class__.__name__}")
        return None
    except Exception as e:
        logger.error(f"Ошибка в LLM: {str(e)}")
        return None

async def process_message(row: dict):
    row = DatasetRow(row)
    
    logger.info("Обработка запроса студента")

    prefix = f'''Описание задачи:
{row.task_condition}\n
Решение студента:
{row.student_solution}\n
Правильное решение (proper_solution):
{row.proper_solution}\n'''

    has_syntax_error, syntax_error = syntax_checker.check_syntax(row.stacktrace if row.stacktrace else "", row.student_solution)
    if has_syntax_error:
        logger.info(f"Обнаружена синтаксическая ошибка: {syntax_error}")
        enhanced_error = f"Ошибка синтаксиса (stacktrace): {syntax_error}"
    else:
        enhanced_error = ""

    if row.stacktrace:
        prefix += f"\nОшибка выполнения: {row.stacktrace}"
    if row.checker_status:
        prefix += f"\nСтатус проверки: {row.checker_status}"
    if enhanced_error and not row.stacktrace:
        prefix += f"\n{enhanced_error}"

    prefix += ""
    logger.info(f"запрос в LLM: {prefix}")

    llm = deepseek_llm
    model_used = "deepseek"
    

    response = await ask_with_timeout(llm, prefix, timeout=12)
    
    if response is None:
        logger.info("DeepSeek не ответил вовремя, запрос в GigaChat")
        llm = gigachat_llm
        model_used = "gigachat"
        response = llm.ask(prefix, clear_history=True)

    if response:
        logger.info(f"Сгенерирован ответ: {response}")
        final_predict = response.replace('\n', ' ').strip()
        final_predict = final_predict.replace("Первое предложение:", "").replace("Продвинутым:", "").replace("Новичкам:", "").replace("Ошибка:", "").replace("Главная ошибка:", "").strip()
        sentences = final_predict.split('. ')
        if len(sentences) >= 2:
            short_hint = sentences[0] + '.'  
            long_hint = sentences[1] + '.'   
        else:
            short_hint = final_predict       
            long_hint = final_predict
    else:
        logger.warning("LLM вернул None")
        short_hint = "LLM не ответил."
        long_hint = ""

    return ResponseData(
        id=row.id,
        short_hint=short_hint,
        long_hint=long_hint,
        model_used=model_used
    )

async def multi_process(tasks: list[dict]):
    tasks_coroutines = [process_message(task.dict()) for task in tasks]
    results = await asyncio.gather(*tasks_coroutines)
    return [
        MultiResponseData(
            id=result.id,
            short_hint=result.short_hint,
            long_hint=result.long_hint,
            model_used=result.model_used
        ) for result in results
    ]