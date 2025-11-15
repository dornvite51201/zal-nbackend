from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    role: str = Field(default="admin")  # 'admin' or 'viewer'


class Series(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    min_value: float
    max_value: float
    color: Optional[str] = None
    icon: Optional[str] = None

    # Przy usunięciu serii usuwamy powiązane rekordy po stronie ORM
    measurements: List["Measurement"] = Relationship(
        back_populates="series",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    sensors: List["Sensor"] = Relationship(
        back_populates="series",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Measurement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # FK do Series
    series_id: int = Field(
        foreign_key="series.id",
        index=True,
    )
    value: float
    timestamp: datetime = Field(index=True)

    series: Optional[Series] = Relationship(back_populates="measurements")


class Sensor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    api_key: str = Field(index=True, unique=True)

    # FK do Series
    series_id: int = Field(
        foreign_key="series.id",
    )

    series: Series = Relationship(back_populates="sensors")