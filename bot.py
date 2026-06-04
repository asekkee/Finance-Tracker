import asyncio
import logging
from typing import Callable, Awaitable, Any

from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, TelegramObject

from config import BOT_TOKEN
from database import init_db
from scheduler import setup_scheduler, register_user
from handlers.expenses import router as expenses_router
from handlers.stats import router as stats_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


class TrackUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable[Any]],
        event: TelegramObject,
        data: dict,
    ) -> Any:
        if hasattr(event, "from_user") and event.from_user:
            register_user(event.from_user.id)
        return await handler(event, data)


async def main():
    init_db()
    log.info("База данных готова")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.message.middleware(TrackUserMiddleware())

    dp.include_router(expenses_router)
    dp.include_router(stats_router)

    @dp.message(CommandStart())
    async def cmd_start(message: Message):
        await message.answer(
            f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
            "Я помогу отслеживать твои расходы.\n\n"
            "<b>Как добавить расход:</b>\n"
            "Просто напиши сумму и описание:\n"
            "<code>2000 кофе</code>\n"
            "<code>15000 продукты</code>\n"
            "<code>3500 такси</code>\n\n"
            "<b>Команды:</b>\n"
            "/today — расходы за сегодня\n"
            "/month — расходы за месяц\n"
            "/help  — справка",
            parse_mode="HTML",
        )

    @dp.message(Command("help"))
    async def cmd_help(message: Message):
        await message.answer(
            "📖 <b>Справка</b>\n\n"
            "<b>Добавить расход:</b>\n"
            "  <code>сумма описание</code>\n"
            "  Примеры: <code>500 кофе</code>, <code>12000 такси</code>\n\n"
            "<b>Команды:</b>\n"
            "  /today — статистика за сегодня\n"
            "  /month — статистика за месяц\n\n"
            "<b>Категории:</b>\n"
            "  🍔 Еда · 🎮 Развлечения · 🚕 Транспорт\n"
            "  📚 Книги · 📈 Инвестиции · 🛍 Другое\n\n"
            "Напоминания приходят в <b>10:00</b> и <b>21:00</b> по Алматы.",
            parse_mode="HTML",
        )

    setup_scheduler(bot)
    log.info("Планировщик запущен")

    log.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
