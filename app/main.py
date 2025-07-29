# app/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.database import init_db
from app.api.routes import auth ,users

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()  # replaces deprecated @app.on_event("startup")
    yield
    # Optional: add shutdown logic here

app = FastAPI(title="CMS Backend", lifespan=lifespan)

# Routers
app.include_router(auth.router,prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/user", tags=["users"])
# Root endpoint


@app.get("/")
async def root():
    return {"message": "CMS is running"}
