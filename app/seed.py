from datetime import datetime, timedelta, timezone
import random
from sqlmodel import Session, select
from .db import engine, init_db
from .models import User, Series, Measurement
from .auth import hash_password

def run():
    init_db()
    with Session(engine) as s:
        # Admin user
        if not s.exec(select(User).where(User.username == "admin")).first():
            s.add(User(username="admin", password_hash=hash_password("admin123"), role="admin"))
            print("Created admin user: admin / admin123")

        # Series
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

        # Measurements
        now = datetime.now(timezone.utc)
        for i in range(100):
            s.add(Measurement(series_id=temp.id, value=round(random.uniform(18, 27), 2), timestamp=now - timedelta(minutes=100 - i)))
            s.add(Measurement(series_id=humid.id, value=round(random.uniform(30, 70), 2), timestamp=now - timedelta(minutes=100 - i)))
        s.commit()
        print("Seeded example series and 200 measurements.")

if __name__ == "__main__":
    run()
