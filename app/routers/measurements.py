from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session, select

from ..db import get_session
from ..deps import require_admin, get_sensor
from ..models import Measurement, Series, Sensor

router = APIRouter(prefix="/measurements", tags=["measurements"])


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class MeasurementBase(BaseModel):
    series_id: int
    value: float
    timestamp: datetime

    def as_utc(self):
        return to_utc(self.timestamp)


class MeasurementCreate(MeasurementBase):
    pass


class MeasurementUpdate(BaseModel):
    series_id: Optional[int] = None
    value: Optional[float] = None
    timestamp: Optional[datetime] = None


class MeasurementRead(MeasurementBase):
    id: int

    class Config:
        from_attributes = True


class SensorMeasurementCreate(BaseModel):
    value: float
    timestamp: Optional[datetime] = None


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


@router.get("", response_model=List[MeasurementRead])
def list_measurements(
    session: Session = Depends(get_session),
    series_id: Optional[int] = Query(None),
    ts_from: Optional[datetime] = Query(None),
    ts_to: Optional[datetime] = Query(None),
    since: Optional[datetime] = Query(None),
    until: Optional[datetime] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    start = ts_from or since
    end = ts_to or until

    if start:
        start = to_utc(start)
    if end:
        end = to_utc(end)

    stmt = select(Measurement)
    if series_id is not None:
        stmt = stmt.where(Measurement.series_id == series_id)
    if start is not None:
        stmt = stmt.where(Measurement.timestamp >= start)
    if end is not None:
        stmt = stmt.where(Measurement.timestamp <= end)
    stmt = stmt.order_by(Measurement.timestamp.asc()).offset(offset).limit(limit)
    return session.exec(stmt).all()


@router.post(
    "",
    response_model=MeasurementRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_measurement(
    data: MeasurementCreate,
    session: Session = Depends(get_session),
):
    _ensure_value_in_range(session, data.series_id, data.value)
    obj = Measurement(
        series_id=data.series_id,
        value=data.value,
        timestamp=data.as_utc(),
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
    obj = session.get(Measurement, measurement_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Measurement not found")
    _ensure_value_in_range(session, data.series_id, data.value)
    obj.series_id = data.series_id
    obj.value = data.value
    obj.timestamp = data.as_utc()
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
    obj = session.get(Measurement, measurement_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Measurement not found")

    payload = data.model_dump(exclude_unset=True)
    new_series_id = payload.get("series_id", obj.series_id)
    new_value = payload.get("value", obj.value)

    _ensure_value_in_range(session, new_series_id, new_value)

    if "timestamp" in payload and payload["timestamp"] is not None:
        payload["timestamp"] = to_utc(payload["timestamp"])

    for k, v in payload.items():
        setattr(obj, k, v)

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
    obj = session.get(Measurement, measurement_id)
    if not obj:
        return
    session.delete(obj)
    session.commit()


@router.post(
    "/from-sensor",
    response_model=MeasurementRead,
    status_code=status.HTTP_201_CREATED,
)
def create_measurement_from_sensor(
    data: SensorMeasurementCreate,
    sensor: Sensor = Depends(get_sensor),
    session: Session = Depends(get_session),
):
    ts = data.timestamp or datetime.now(timezone.utc)
    ts = to_utc(ts)
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
