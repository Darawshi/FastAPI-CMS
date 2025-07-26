# app/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.database import init_db
from app.api.routes import auth
from app.core import events  # noqa: F401 (ensures event listeners are registered)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()  # replaces deprecated @app.on_event("startup")
    yield
    # Optional: add shutdown logic here

app = FastAPI(title="CMS Backend", lifespan=lifespan)

# Routers
app.include_router(auth.router, tags=["auth"])

# Root endpoint
@app.get("/")
async def root():
    return {"message": "CMS is running"}
