from fastapi import FastAPI
from app.core.database import init_db
from app.api import auth

app = FastAPI(title="CMS Backend")


@app.on_event("startup")
async def on_startup():
    await init_db()


app.include_router(auth.router, tags=["auth"])


@app.on_event("startup")
async def on_startup():
    await init_db()


@app.get("/")
async def root():
    return {"message": "CMS is running"}
