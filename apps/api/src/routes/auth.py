from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from datetime import timedelta

from ..database import get_db
from ..schemas.user import UserCreate, UserLogin, UserOut, TokenOut
from ..services.auth_service import (
    create_user, authenticate_user, create_access_token,
    get_user_by_email, decode_token, get_user_by_id,
)
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def get_admin_user(current_user=Depends(get_current_user)):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


@router.post("/signup", response_model=dict, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, response: Response, db: Session = Depends(get_db)):
    existing = get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = create_user(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        country=payload.country,
    )

    token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return {
        "data": TokenOut(
            access_token=token,
            user=UserOut.model_validate(user),
        ).model_dump(),
        "message": "Account created successfully",
    }


@router.post("/login", response_model=dict)
def login(payload: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return {
        "data": TokenOut(
            access_token=token,
            user=UserOut.model_validate(user),
        ).model_dump(),
        "message": "Logged in successfully",
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"data": None, "message": "Logged out successfully"}


@router.get("/me", response_model=dict)
def me(current_user=Depends(get_current_user)):
    return {
        "data": UserOut.model_validate(current_user).model_dump(),
        "message": "OK",
    }
