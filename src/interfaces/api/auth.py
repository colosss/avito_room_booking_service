from fastapi import APIRouter, Depends, HTTPException
from src.infrastructure.database.db_helper import db_helper
from src.infrastructure.database.repositories.users import UserRepository
from src.application.use_case.auth import(
    LoginUseCase,
    RegisterUseCase,
    DummyLoginUseCase,
)
from src.application.dto.auth import (
    DummyLogintDTO,
    LoginDTO,
    RegisterDTO,
    TokenSchema,
    UserSchema,
)

router=APIRouter(tags=["Auth"])

@router.get("/_info")
async def info():
    return {"status": "ok"}

@router.post("/dummyLogin", response_model=TokenSchema)
async def dummy_login(
    body: DummyLogintDTO,
    session=Depends(db_helper.session_dependency)):
    try:
        token=await DummyLoginUseCase(UserRepository(session=session).execute(body.role))
    except ValueError as e:
        raise HTTPException(400, detail={"error": {"code": "INVALID_REQUEST", "message": str(e)}})
    return TokenSchema(token=token)


@router.post("/register", response_model=UserSchema, status_code=201)
async def register(
    body: RegisterDTO, 
    session=Depends(db_helper.session_dependency)):
    try:
        user=await RegisterUseCase(UserRepository(session=session)).execute(
            body.email,
            body.password,
        )
    except ValueError as e:
        raise HTTPException(409, detail={"error": {"code": str(e), "message": str(e)}})
    return UserSchema(id=str(user.id), email=user.email, role=user.role)

@router.post("/login", response_model=TokenSchema)
async def loggin(
    body: LoginDTO,
    session=Depends(db_helper.session_dependency)):
    try:
        token=await LoginUseCase(UserRepository(session=session)).execute(
            body.email,
            body.password,
        )
    except ValueError:
        raise HTTPException(401, detail={"error": {"code": "INVALID_CREDENTIALS","message": "invalid credentials"}})
    return TokenSchema(token=token)