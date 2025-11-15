import time
import random
import requests
from datetime import datetime

SENSOR_KEY = "TWÓJ_PRAWDZIWY_API_KEY"

# Adres backendu – lokalnie:
API_URL = "http://localhost:8000/measurements/from-sensor"
# Przy wdrożeniu podmień na publiczny URL backendu.

# Wstaw tu klucz wygenerowany przy POST /sensors
SENSOR_KEY = "WKLEJ_TUTAJ_API_KEY"

def generate_value() -> float:
    # Przykładowe dane: np. temperatura 20–25
    return round(random.uniform(20.0, 25.0), 2)

def main():
    print("Fake sensor started. Ctrl+C aby przerwać.")
    while True:
        value = generate_value()
        payload = {
            "value": value,
            # timestamp opcjonalny – pokazujemy jawnie żeby było czytelne
            "timestamp": datetime.utcnow().isoformat(),
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
                    f"[OK] {datetime.utcnow().isoformat()} -> "
                    f"value={value}, id={data['id']}, series={data['series_id']}"
                )
            else:
                print(f"[ERR] {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[ERR] {e}")

        time.sleep(5)  # wysyłaj co 5 sekund

if __name__ == "__main__":
    main()