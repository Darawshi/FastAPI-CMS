#app/tasks/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.auth.token_cleanup import delete_expired_tokens
from app.core.database import async_session

scheduler = AsyncIOScheduler()

def start_scheduler():
    scheduler.start()
    scheduler.add_job(
        clean_expired_tokens_job,
        trigger=IntervalTrigger(minutes=10),
        id="cleanup_expired_tokens",
        replace_existing=True,
    )
    print("[Scheduler] APScheduler started")

def shutdown_scheduler():
    scheduler.shutdown(wait=False)
    print("[Scheduler] APScheduler shutdown")

async def clean_expired_tokens_job():
    async with async_session() as session:
        count = await delete_expired_tokens(session)
        print(f"[Scheduler] Deleted {count} expired password reset tokens")