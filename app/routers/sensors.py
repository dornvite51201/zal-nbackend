import secrets
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from ..db import get_session
from ..deps import require_admin
from ..models import Sensor, Series

router = APIRouter(prefix="/sensors", tags=["sensors"])


class SensorCreate(BaseModel):
    name: str
    series_id: int


class SensorRead(BaseModel):
    id: int
    name: str
    series_id: int

    class Config:
        from_attributes = True


class SensorWithKey(SensorRead):
    api_key: str


@router.get(
    "",
    response_model=List[SensorRead],
    dependencies=[Depends(require_admin)],
)
def list_sensors(session: Session = Depends(get_session)):
    """Lista zarejestrowanych sensorów (bez kluczy API)."""
    return session.exec(select(Sensor)).all()


@router.post(
    "",
    response_model=SensorWithKey,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_sensor(
    data: SensorCreate,
    session: Session = Depends(get_session),
):
    """Utwórz nowy sensor i wygeneruj dla niego klucz API."""
    series = session.get(Series, data.series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    api_key = secrets.token_hex(16)

    sensor = Sensor(
        name=data.name,
        series_id=data.series_id,
        api_key=api_key,
    )
    session.add(sensor)
    session.commit()
    session.refresh(sensor)


    return SensorWithKey.model_validate(sensor)