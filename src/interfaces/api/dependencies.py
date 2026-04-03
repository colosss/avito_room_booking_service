from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.infrastructure.auth.jwt import decode_token

bearer = HTTPBearer()

def get_current_user(
        credentials: HTTPAuthorizationCredentials=Depends(bearer)
)->dict:
    try:
        payload=decode_token(credentials.credentials)
        return{"user_id": payload["user_id"], "role": payload["role"]}
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "invalid token"}}
        )
    
def require_admin(current_user: dict = Depends(get_current_user))->dict:
    if current_user["role"]!="admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "admin role required"}},
        )
    return current_user

def require_user(current_user: dict=Depends(get_current_user))->dict:
    if current_user["role"]!="user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "admin role required"}},
        )
    return current_user