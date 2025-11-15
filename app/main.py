import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .routers import auth as auth_router
from .routers import series as series_router
from .routers import measurements as measurements_router
from .routers.sensors import router as sensors_router
from .errors import setup_error_handlers

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app = FastAPI(title="Measurements API (FastAPI + SQLite)")
setup_error_handlers(app)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "version": "1.0.0"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(auth_router.router)
app.include_router(series_router.router)
app.include_router(measurements_router.router)
app.include_router(sensors_router)