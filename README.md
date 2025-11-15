# FastAPI + SQLite Starter (Measurements API)

Prosty backend REST (poziom 2) dla projektu: serie pomiarowe + pomiary, walidacja min/max, logowanie admina (JWT), auto-dokumentacja Swagger.

## Wymagania
- Python 3.11+
- (Opcjonalnie) virtualenv

## Instalacja
```bash
cd fastapi-sqlite-starter
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edytuj SECRET_KEY na długi losowy string
```

## Uruchomienie
```bash
uvicorn app.main:app --reload
```
Aplikacja wystartuje na `http://127.0.0.1:8000`. Dokumentacja Swagger: `http://127.0.0.1:8000/docs`.

## Seed danych (admin + przykładowe serie/pomiary)
```bash
python -m app.seed
```
Utworzy użytkownika admina: `admin / admin123` oraz 2 serie i 200 pomiarów.

## Endpoints (skrót)
- `POST /auth/login` (OAuth2PasswordRequestForm: `username`, `password`) → zwraca JWT.
- `GET /series` (publiczny)
- `POST /series` (admin) – tworzenie, waliduje `min_value <= max_value`.
- `PUT /series/{id}` (admin), `DELETE /series/{id}` (admin)
- `GET /measurements?series_id=&ts_from=&ts_to=` (publiczny; ISO 8601 dla dat)
- `POST /measurements` (admin) – odrzuca wartości spoza min/max serii (422).

## Uwierzytelnianie
Wykorzystuje schemat OAuth2 password flow (JWT Bearer).
- Najpierw `POST /auth/login` (form-data), potem do zapytań admina dodaj nagłówek:
```
Authorization: Bearer <token>
```

## Konfiguracja CORS
W `app/main.py` dopasuj `allow_origins` do domeny frontendu w produkcji.

## Deploy (ogólny)
- Utwórz obraz Dockera albo uruchom na serwisie typu Render / Railway.
- Ustaw zmienne środowiskowe z `.env`.
- Pamiętaj o trwałym wolumenie dla pliku SQLite, jeśli dane mają przetrwać restart.

## Struktura
```
app/
  main.py          # FastAPI + routing + CORS
  db.py            # engine, init_db, get_session()
  models.py        # tabele (User, Series, Measurement)
  schemas.py       # Pydantic (wejście/wyjście)
  auth.py          # hashowanie + JWT
  deps.py          # zależności: current_user, require_admin
  routers/
    auth.py
    series.py
    measurements.py
  seed.py          # skrypt do zasiania danych
```

Powodzenia! 🙂
