from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response, Query, status
from sqlmodel import Session, select, func
from ..db import get_session
from ..deps import require_admin
from ..models import Series, Measurement, Sensor
from ..schemas import SeriesCreate, SeriesRead, SeriesUpdate

router = APIRouter(prefix="/series", tags=["series"])

@router.get("", response_model=List[SeriesRead])
def list_series(
    response: Response,
    session: Session = Depends(get_session),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    total = session.exec(select(func.count(Series.id))).one()
    response.headers["X-Total-Count"] = str(total)
    return session.exec(select(Series).order_by(Series.id).offset(offset).limit(limit)).all()

@router.post(
    "",
    response_model=SeriesRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_series(data: SeriesCreate, session: Session = Depends(get_session)):
    if data.min_value > data.max_value:
        raise HTTPException(status_code=422, detail="min_value must be <= max_value")
    obj = Series(**data.dict())
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj

@router.put(
    "/{series_id}",
    response_model=SeriesRead,
    dependencies=[Depends(require_admin)],
)
def update_series(series_id: int, data: SeriesUpdate, session: Session = Depends(get_session)):
    obj = session.get(Series, series_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Series not found")

    payload = data.dict(exclude_unset=True)
    new_min = payload.get("min_value", obj.min_value)
    new_max = payload.get("max_value", obj.max_value)
    if new_min > new_max:
        raise HTTPException(status_code=422, detail="min_value must be <= max_value")

    for k, v in payload.items():
        setattr(obj, k, v)

    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj

@router.delete(
    "/{series_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_series(series_id: int, session: Session = Depends(get_session)):
    obj = session.get(Series, series_id)
    if not obj:
        return
    children_meas = session.exec(select(Measurement).where(Measurement.series_id == series_id)).all()
    for m in children_meas:
        session.delete(m)
    children_sens = session.exec(select(Sensor).where(Sensor.series_id == series_id)).all()
    for s in children_sens:
        session.delete(s)
    session.delete(obj)
    session.commit()