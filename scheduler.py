from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from database import get_today_expenses

scheduler = AsyncIOScheduler(timezone="Asia/Almaty")

# Список user_id кто получит напоминание.
# В реальном боте это берётся из БД (все пользователи кто писал боту).
_active_users: set[int] = set()


def register_user(user_id: int):
    """Вызывается при любом сообщении от пользователя."""
    _active_users.add(user_id)


def setup_scheduler(bot: Bot):

    @scheduler.scheduled_job("cron", hour=10, minute=0)
    async def morning_reminder():
        for uid in _active_users:
            try:
                await bot.send_message(
                    uid,
                    "☀️ Доброе утро! Не забывайте записывать расходы сегодня.\n\n"
                    "Пример: <b>500 кофе</b>",
                    parse_mode="HTML",
                )
            except Exception:
                pass

    @scheduler.scheduled_job("cron", hour=21, minute=0)
    async def evening_reminder():
        for uid in _active_users:
            try:
                expenses = get_today_expenses(uid)
                if expenses:
                    total = sum(e["amount"] for e in expenses)
                    await bot.send_message(
                        uid,
                        f"🌙 Итог дня: потрачено <b>{total:,} тг</b> в {len(expenses)} транзакциях.\n\n"
                        f"Посмотреть детали: /today",
                        parse_mode="HTML",
                    )
                else:
                    await bot.send_message(
                        uid,
                        "🌙 Сегодня расходов не записано. Всё под контролем? 😊",
                    )
            except Exception:
                pass

    scheduler.start()