from pydantic import BaseModel, ConfigDict

class DummyLogintDTO(BaseModel):
    role: str

class RegisterDTO(BaseModel):
    email: str
    password: str
    role:str = "user"

class LoginDTO(BaseModel):
    email: str
    password: str

class TokenSchema(BaseModel):
    token: str

class UserSchema(BaseModel):
    id: str
    email: str
    role:str