from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from ..db import get_session
from ..deps import require_admin, get_sensor
from ..models import Measurement, Series, Sensor

router = APIRouter(prefix="/measurements", tags=["measurements"])


# ---------- Schemy Pydantic (request/response) ----------


class MeasurementBase(BaseModel):
    series_id: int
    value: float
    timestamp: datetime


class MeasurementCreate(MeasurementBase):
    """Pełne dane potrzebne do utworzenia / zastąpienia pomiaru."""
    pass


class MeasurementUpdate(BaseModel):
    """Częściowa aktualizacja (PATCH)."""
    series_id: Optional[int] = None
    value: Optional[float] = None
    timestamp: Optional[datetime] = None


class MeasurementRead(MeasurementBase):
    id: int

    class Config:
        from_attributes = True


class SensorMeasurementCreate(BaseModel):
    """Dane wysyłane przez sensor.

    series_id NIE jest tu podawane – jest powiązane z sensorem.
    """
    value: float
    timestamp: Optional[datetime] = None


# ---------- Pomocnicza walidacja zakresu ----------


def _ensure_value_in_range(session: Session, series_id: int, value: float) -> Series:
    series = session.get(Series, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    if value < series.min_value or value > series.max_value:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Value {value} out of range "
                f"[{series.min_value}, {series.max_value}] for series '{series.name}'"
            ),
        )
    return series


# ---------- Endpointy ----------


@router.get("", response_model=List[MeasurementRead])
def list_measurements(
    session: Session = Depends(get_session),
    series_id: Optional[int] = Query(
        None, description="Filtr po ID serii"
    ),
    ts_from: Optional[datetime] = Query(
        None, description="Początek zakresu czasu (>= ts_from)"
    ),
    ts_to: Optional[datetime] = Query(
        None, description="Koniec zakresu czasu (<= ts_to)"
    ),
    # aliasy dla zgodności wstecznej (opcjonalne)
    since: Optional[datetime] = Query(
        None, description="DEPRECATED: użyj ts_from"
    ),
    until: Optional[datetime] = Query(
        None, description="DEPRECATED: użyj ts_to"
    ),
    limit: int = Query(
        200, ge=1, le=1000, description="Limit wyników"
    ),
    offset: int = Query(
        0, ge=0, description="Przesunięcie (paginacja)"
    ),
):
    """
    Lista pomiarów.

    - filtrowanie po `series_id`
    - filtrowanie po czasie (`ts_from` / `ts_to`)
    - poprawne kody HTTP, sortowanie po timestamp rosnąco
    """
    start = ts_from or since
    end = ts_to or until

    stmt = select(Measurement)

    if series_id is not None:
        stmt = stmt.where(Measurement.series_id == series_id)
    if start is not None:
        stmt = stmt.where(Measurement.timestamp >= start)
    if end is not None:
        stmt = stmt.where(Measurement.timestamp <= end)

    stmt = (
        stmt.order_by(Measurement.timestamp.asc())
        .offset(offset)
        .limit(limit)
    )
    return session.exec(stmt).all()


@router.post(
    "",
    response_model=MeasurementRead,
    dependencies=[Depends(require_admin)],
)
def create_measurement(
    data: MeasurementCreate,
    session: Session = Depends(get_session),
):
    """
    Utworzenie nowego pomiaru (tylko admin).

    Walidacja min/max na podstawie serii.
    """
    _ensure_value_in_range(session, data.series_id, data.value)

    obj = Measurement(
        series_id=data.series_id,
        value=data.value,
        timestamp=data.timestamp,
    )
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.put(
    "/{measurement_id}",
    response_model=MeasurementRead,
    dependencies=[Depends(require_admin)],
)
def replace_measurement(
    measurement_id: int,
    data: MeasurementCreate,
    session: Session = Depends(get_session),
):
    """
    Pełne zastąpienie istniejącego pomiaru (PUT).

    - wymaga kompletnych danych MeasurementCreate,
    - walidacja min/max.
    """
    obj = session.get(Measurement, measurement_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Measurement not found")

    _ensure_value_in_range(session, data.series_id, data.value)

    obj.series_id = data.series_id
    obj.value = data.value
    obj.timestamp = data.timestamp

    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.patch(
    "/{measurement_id}",
    response_model=MeasurementRead,
    dependencies=[Depends(require_admin)],
)
def update_measurement(
    measurement_id: int,
    data: MeasurementUpdate,
    session: Session = Depends(get_session),
):
    """
    Częściowa aktualizacja (PATCH).

    Też waliduje min/max, jeśli zmieniamy serię lub wartość.
    """
    obj = session.get(Measurement, measurement_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Measurement not found")

    payload = data.model_dump(exclude_unset=True)

    new_series_id = payload.get("series_id", obj.series_id)
    new_value = payload.get("value", obj.value)

    _ensure_value_in_range(session, new_series_id, new_value)

    for field, value in payload.items():
        setattr(obj, field, value)

    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


@router.delete(
    "/{measurement_id}",
    status_code=204,
    dependencies=[Depends(require_admin)],
)
def delete_measurement(
    measurement_id: int,
    session: Session = Depends(get_session),
):
    """
    Usunięcie pomiaru (tylko admin).
    204 – brak treści, jeśli OK.
    """
    obj = session.get(Measurement, measurement_id)
    if not obj:
        return
    session.delete(obj)
    session.commit()


@router.post(
    "/from-sensor",
    response_model=MeasurementRead,
)
def create_measurement_from_sensor(
    data: SensorMeasurementCreate,
    sensor: Sensor = Depends(get_sensor),
    session: Session = Depends(get_session),
):
    """
    Endpoint dla autonomicznych sensorów.

    - autoryzacja przez nagłówek X-Sensor-Key
    - sensor przypisany do jednej serii (sensor.series_id)
    - timestamp opcjonalny (domyślnie bieżący czas)
    - walidacja min/max na podstawie serii
    """
    ts = data.timestamp or datetime.utcnow()

    _ensure_value_in_range(session, sensor.series_id, data.value)

    obj = Measurement(
        series_id=sensor.series_id,
        value=data.value,
        timestamp=ts,
    )
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj