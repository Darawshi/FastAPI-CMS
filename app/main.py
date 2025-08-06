# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.api.routes import auth ,users
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
app.include_router(auth.router,prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/user", tags=["users"])
# Root endpoint


@app.get("/")
async def root():
    return {"message": "CMS is running"}
