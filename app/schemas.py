from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# Auth
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    sub: str | None = None
    role: str | None = None

class LoginRequest(BaseModel):
    username: str
    password: str

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str   


# Series
class SeriesBase(BaseModel):
    name: str
    min_value: float
    max_value: float
    color: str | None = None
    icon: str | None = None

class SeriesCreate(SeriesBase): 
    pass
class SeriesUpdate(SeriesBase): 
    pass

class SeriesRead(SeriesBase):
    id: int

# Measurement
class MeasurementBase(BaseModel):
    series_id: int
    value: float
    timestamp: datetime

class MeasurementCreate(MeasurementBase): 
    pass

class MeasurementRead(MeasurementBase):
    id: int
