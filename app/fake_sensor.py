import time
import random
import requests
from datetime import datetime

API_URL = "http://127.0.0.1:8000/measurements/from-sensor"
SENSOR_KEY = "bce5dcbd5fd2f8b334974d4ac2ed6dd7"


def generate_value() -> float:
    return round(random.uniform(20.0, 25.0), 2)


def main():
    print("Fake sensor started. Ctrl+C aby przerwać.")
    while True:
        value = generate_value()
        payload = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
        }
        headers = {
            "X-Sensor-Key": SENSOR_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            resp = requests.post(API_URL, json=payload, headers=headers, timeout=5)
            if resp.status_code in (200, 201):
                data = resp.json()
                print(
                    f"[OK] {datetime.now().isoformat()} -> "
                    f"value={value}, id={data['id']}, series={data['series_id']}"
                )
            else:
                print(f"[ERR] {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[ERR] {e}")

        time.sleep(5)


if __name__ == "__main__":
    main()
