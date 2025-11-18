# Measurements API (FastAPI/SQLite)

1. Uruchomienie lokalne

  1.1. Wymagania:
- Python 3.11 lub nowszy  
- `pip` (menedżer pakietów Pythona)

2. Instalacja 

Wszystkie komendy wykonujemy w katalogu `backend`.

  2.1. Wejście do katalogu:

   cd backend 
   # przykład pełnej ścieżki:
   # cd C:\Users\monik\Downloads\projekt-zal\backend

  2.2. Utworzenie i aktywacja wirtualnego środowiska

  - Windows (PowerShell) (rekomendowane):
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1 
  # opcjonalnie w przypadku użycia konsoli cmd: .venv\Scripts\activate

  - Linux / macOS:
  python -m venv .venv
  source .venv/bin/activate

  2.3. Instalacja zależności: 
  pip install -r requirements.txt

  2.4. Plik .env jest już skonfigurowany do uruchomienia lokalnego.

  3. (Opcjonalnie) Seed danych (użytkownik admin + przykładowe serie/pomiary)
  python -m app.seed

  Utworzy to m.in. użytkownika: login: admin / hasło: admin123 oraz przykładowe serie i pomiary.

  4. Uruchomienie backendu lokalnie w aktywnym środowisku wirtualnym (.venv)
  uvicorn app.main:app --reload
  
  -> Domyślnie aplikacja dostępna pod:
  - API: http://127.0.0.1:8000/docs
  - dokumentacja Swagger: http://127.0.0.1:8000/docs

  -> Uruchomienie wersji wdrożonej (hosting):
  Backend został wdrożony na Render.com.
  - URL API: https://zal-nbackend.onrender.com
  - Dokumentacja Swagger: https://zal-nbackend.onrender.com/docs
  Frontend (SPA) używa tego adresu jako VITE_API_URL.

  