# app/auth.py
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import jwt, JWTError
from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY", "change_me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

PEPPER = os.getenv("PASSWORD_PEPPER", "")

pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")


def _mix(pw: str) -> str:
    return pw + PEPPER


def hash_password(password: str) -> str:
    return pwd_context.hash(_mix(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(_mix(plain_password), hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
