"""
APSchedulerを使った毎日の定期更新スケジューラ。
単独で `python scheduler.py` で起動するか、
Flaskアプリと一緒に起動する。
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config import UPDATE_HOUR, UPDATE_MINUTE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_scheduler = None


def get_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="Asia/Tokyo")
    return _scheduler


def _daily_update_with_email():
    from updater import run_daily_update
    run_daily_update(force_email=True)


def start_scheduler():
    sched = get_scheduler()
    if sched.running:
        return sched

    sched.add_job(
        _daily_update_with_email,
        trigger=CronTrigger(hour=UPDATE_HOUR, minute=UPDATE_MINUTE, timezone="Asia/Tokyo"),
        id="daily_update",
        replace_existing=True,
    )
    sched.start()
    logger.info(f"スケジューラ起動: 毎日 {UPDATE_HOUR:02d}:{UPDATE_MINUTE:02d} JST に更新実行")
    return sched


def stop_scheduler():
    sched = get_scheduler()
    if sched.running:
        sched.shutdown()
        logger.info("スケジューラ停止")


if __name__ == "__main__":
    import time
    from updater import run_daily_update

    logger.info("初回更新を実行中...")
    run_daily_update()

    start_scheduler()
    logger.info("スケジューラ稼働中 (Ctrl+C で停止)")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        stop_scheduler()
