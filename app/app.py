from fastapi import FastAPI, HTTPException, Response, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from hashlib import md5
import logging
import uvicorn

from config import get_config
from main_processing import process_message, multi_process  # Убран префикс app., если он не нужен
from schemas import RequestData, ResponseData, MultiRequestData, MultiResponseData, UserLoginSchema
from auth.auth_handler import sign_jwt, JWTBearer
import logging_config

config = get_config()
logger = logging.getLogger(__name__)
logger.info(f"Конфигурация загружена: {config}")

app = FastAPI(
    title="AI Python Assistant",
    version="0.0.1",
    root_path="/aiassistant",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def check_user(data: UserLoginSchema):
    for username, password_hash in config.allowed_users.items():
        if username == data.username and password_hash == md5(data.password.encode('utf-8')).hexdigest():
            return True
    return False

@app.post("/auth")
async def auth(user: UserLoginSchema = Body(...)):
    logger.info(f"Попытка аутентификации для пользователя: {user.username}")
    if check_user(user):
        token = sign_jwt(user.username)
        logger.info(f"Успешная аутентификация, токен выдан: {token}")
        return token
    logger.warning("Неудачная аутентификация: неверные данные")
    return {"error": "Wrong login details"}

@app.post("/process", response_model=ResponseData, dependencies=[Depends(JWTBearer())])
async def process_data(request_data: RequestData):
    logger.info(f"Получен запрос: {request_data.model_dump()}")  # Замена .dict() на .model_dump()
    try:
        response_data = await process_message(request_data.model_dump())  # Замена .dict() на .model_dump()
        if not response_data.short_hint or not response_data.long_hint:
            logger.warning("process_message вернул пустой результат")
            raise ValueError("Не удалось обработать запрос")
        logger.info(f"Результат обработки: short_hint={response_data.short_hint}, long_hint={response_data.long_hint}")
        return response_data
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")

@app.post("/multi_process", response_model=list[MultiResponseData], dependencies=[Depends(JWTBearer())])
async def multi_process_data(request_data: MultiRequestData):
    logger.info(f"Получен множественный запрос: {len(request_data.tasks)} задач")
    try:
        results = await multi_process(request_data.tasks)
        logger.info(f"Обработано {len(results)} задач")
        return results
    except Exception as e:
        logger.error(f"Ошибка при обработке множественного запроса: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")

@app.get("/ping")
async def ping():
    logger.info("Получен запрос на /ping")
    return Response(content="pong", status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)