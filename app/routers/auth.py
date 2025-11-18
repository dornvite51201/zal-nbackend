from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from sqlmodel import Session, select

from ..schemas import Token, PasswordChangeRequest
from ..models import User
from ..auth import verify_password, create_access_token, hash_password
from ..db import get_session
from ..deps import get_current_user

import time

router = APIRouter(prefix="/auth", tags=["auth"])

BUCKET: dict[str, list[float]] = {}
WINDOW = 300
MAX_TRIES = 10


def guard_rate_limit(ip: str) -> None:
    now = time.time()
    if ip not in BUCKET:
        BUCKET[ip] = []
    BUCKET[ip] = [t for t in BUCKET[ip] if now - t < WINDOW]
    if len(BUCKET[ip]) >= MAX_TRIES:
        raise HTTPException(status_code=429, detail="Too many login attempts, try later")
    BUCKET[ip].append(now)


class LoginJSON(BaseModel):
    username: str
    password: str


def _do_login(username: str, password: str, session: Session) -> Token:
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": user.username, "role": user.role})
    return Token(access_token=token, token_type="bearer")


@router.post("/login", response_model=Token)
def login_json(
    body: LoginJSON,
    request: Request,
    session: Session = Depends(get_session),
):
    ip = request.client.host if request.client else "unknown"
    guard_rate_limit(ip)
    return _do_login(body.username, body.password, session)


@router.post("/token", response_model=Token)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    session: Session = Depends(get_session),
):
    ip = request.client.host if request.client else "unknown"
    guard_rate_limit(ip)
    return _do_login(form_data.username, form_data.password, session)


@router.post("/change-password", status_code=204)
def change_password(
    body: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not verify_password(body.old_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password")
    current_user.password_hash = hash_password(body.new_password)
    session.add(current_user)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
