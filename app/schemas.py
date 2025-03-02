from pydantic import BaseModel, Field

class RequestData(BaseModel):
    id: str = ''
    task_condition: str = ''
    student_solution: str = ''
    stacktrace: str = ''
    proper_solution: str = ''

class MultiRequestData(BaseModel):
    tasks: list[RequestData]

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

class UserLoginSchema(BaseModel):
    username: str = Field(...)
    password: str = Field(...)

    class Config:
        json_schema_extra = {
            "example": {
                "username": "smartlms",
                "password": "3q88cFQx5"
            }
        }