from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from ..schemas import Token, PasswordChangeRequest
from ..models import User
from ..auth import verify_password, create_access_token, hash_password
from ..db import get_session
from ..deps import get_current_user

import time

router = APIRouter(prefix="/auth", tags=["auth"])

BUCKET = {}          # ip -> [timestamps]
WINDOW = 300         # 5 minut
MAX_TRIES = 10

def guard_rate_limit(ip: str):
    now = time.time()
    BUCKET.setdefault(ip, [])
    BUCKET[ip] = [t for t in BUCKET[ip] if now - t < WINDOW]
    if len(BUCKET[ip]) >= MAX_TRIES:
        raise HTTPException(status_code=429, detail="Too many login attempts, try later")
    BUCKET[ip].append(now)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
def login(
    request: Request,                                   # ← DODANE
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    guard_rate_limit(request.client.host)               # ← DODANE

    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/change-password", status_code=204)
def change_password(
    body: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    # Sprawdź stare hasło
    if not verify_password(body.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    # Ustaw nowe hasło
    current_user.password_hash = hash_password(body.new_password)
    session.add(current_user)
    session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)