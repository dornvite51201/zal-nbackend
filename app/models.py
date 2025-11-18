from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Integer, ForeignKey


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    role: str = Field(default="admin")


class Series(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    min_value: float
    max_value: float
    color: Optional[str] = None
    icon: Optional[str] = None

    measurements: List["Measurement"] = Relationship(
        back_populates="series",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
        },
    )
    sensors: List["Sensor"] = Relationship(
        back_populates="series",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
        },
    )


class Measurement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    series_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("series.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    value: float
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )

    series: Optional[Series] = Relationship(back_populates="measurements")


class Sensor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    api_key: str = Field(index=True, unique=True)
    series_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("series.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )

    series: Optional[Series] = Relationship(back_populates="sensors")
