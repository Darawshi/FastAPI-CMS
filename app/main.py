# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.routes.api import api_router
from app.tasks.scheduler import start_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ✅ Startup logic
    await init_db()
    start_scheduler()

    yield  # 👈 Only one yield allowed!

    # ✅ Shutdown logic
    shutdown_scheduler()
app = FastAPI(title="CMS Backend", lifespan=lifespan)
# Routers
app.include_router(api_router)  # just include the master router here


@app.get("/")
async def root():
    return {"message": "CMS is running"}


