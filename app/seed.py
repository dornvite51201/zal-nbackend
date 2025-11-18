from datetime import datetime, timedelta, timezone
import random
import secrets

from sqlmodel import Session, select

from .db import engine, init_db
from .models import User, Series, Measurement, Sensor
from .auth import hash_password


def run() -> None:
    init_db()
    with Session(engine) as s:
        admin = s.exec(select(User).where(User.username == "admin")).first()
        if not admin:
            s.add(User(username="admin", password_hash=hash_password("admin123"), role="admin"))
            s.commit()
            print("Created admin user: admin / admin123")

        temp = s.exec(select(Series).where(Series.name == "Temperature")).first()
        if not temp:
            temp = Series(name="Temperature", min_value=15.0, max_value=30.0, color="#ff0000", icon="thermometer")
            s.add(temp)
            s.commit()
            s.refresh(temp)

        humid = s.exec(select(Series).where(Series.name == "Humidity")).first()
        if not humid:
            humid = Series(name="Humidity", min_value=20.0, max_value=80.0, color="#0000ff", icon="droplet")
            s.add(humid)
            s.commit()
            s.refresh(humid)

        now = datetime.now(timezone.utc)

        has_temp = s.exec(select(Measurement.id).where(Measurement.series_id == temp.id).limit(1)).first() if temp else True
        has_humid = s.exec(select(Measurement.id).where(Measurement.series_id == humid.id).limit(1)).first() if humid else True

        if temp and not has_temp:
            for i in range(100):
                s.add(
                    Measurement(
                        series_id=temp.id,
                        value=round(random.uniform(18, 27), 2),
                        timestamp=now - timedelta(minutes=100 - i),
                    )
                )

        if humid and not has_humid:
            for i in range(100):
                s.add(
                    Measurement(
                        series_id=humid.id,
                        value=round(random.uniform(30, 70), 2),
                        timestamp=now - timedelta(minutes=100 - i),
                    )
                )

        s.commit()

        if temp:
            sensor = s.exec(select(Sensor).where(Sensor.series_id == temp.id)).first()
            if not sensor:
                sensor = Sensor(name="Temp Sensor", series_id=temp.id, api_key=secrets.token_hex(16))
                s.add(sensor)
                s.commit()
                s.refresh(sensor)
            print(f"Sensor for 'Temperature': id={sensor.id}, api_key={sensor.api_key}")

        print("Seed complete.")


if __name__ == "__main__":
    run()