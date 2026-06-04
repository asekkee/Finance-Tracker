from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import get_today_expenses, get_month_expenses

router = Router()

CAT_LABELS = {
    "food":      "🍔 Еда",
    "fun":       "🎮 Развлечения",
    "transport": "🚕 Транспорт",
    "books":     "📚 Книги",
    "invest":    "📈 Инвестиции",
    "other":     "🛍 Другое",
}


def build_category_summary(expenses: list[dict]) -> dict:
    summary = {}
    for e in expenses:
        cat = e["category"]
        summary[cat] = summary.get(cat, 0) + e["amount"]
    return summary


@router.message(Command("today"))
async def cmd_today(message: Message):
    expenses = get_today_expenses(message.from_user.id)

    if not expenses:
        await message.answer("📭 Сегодня расходов ещё нет.\n\nДобавьте: <b>2000 кофе</b>", parse_mode="HTML")
        return

    total = sum(e["amount"] for e in expenses)
    by_cat = build_category_summary(expenses)

    lines = ["📊 <b>Сегодня</b>\n", f"💰 <b>Всего: {total:,} тг</b>\n"]

    for cat_id, amount in sorted(by_cat.items(), key=lambda x: -x[1]):
        label = CAT_LABELS.get(cat_id, "🛍 Другое")
        pct = round(amount / total * 100)
        lines.append(f"{label}: <b>{amount:,} тг</b> ({pct}%)")

    lines.append("\n<i>Последние транзакции:</i>")
    for e in expenses[:10]:  # показываем до 10
        time_str = e["created_at"][11:16]  # HH:MM
        label = CAT_LABELS.get(e["category"], "🛍 Другое")
        lines.append(f"  {time_str} · {e['description']} · {e['amount']:,} тг · {label}")

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("month"))
async def cmd_month(message: Message):
    expenses = get_month_expenses(message.from_user.id)

    if not expenses:
        await message.answer("📭 В этом месяце расходов нет.\n\nДобавьте: <b>2000 кофе</b>", parse_mode="HTML")
        return

    total = sum(e["amount"] for e in expenses)
    days = len(set(e["created_at"][:10] for e in expenses))
    avg_per_day = total // days if days else 0
    by_cat = build_category_summary(expenses)
    top_cat_id = max(by_cat, key=by_cat.get)
    top_cat_label = CAT_LABELS.get(top_cat_id, "🛍 Другое")
    top_cat_amount = by_cat[top_cat_id]
    top_cat_pct = round(top_cat_amount / total * 100)

    lines = [
        "📈 <b>За этот месяц</b>\n",
        f"💰 Всего: <b>{total:,} тг</b>",
        f"📅 Дней с расходами: <b>{days}</b>",
        f"📊 Среднее в день: <b>{avg_per_day:,} тг</b>",
        f"🏆 Топ категория: <b>{top_cat_label}</b> — {top_cat_amount:,} тг ({top_cat_pct}%)\n",
        "<i>По категориям:</i>",
    ]

    for cat_id, amount in sorted(by_cat.items(), key=lambda x: -x[1]):
        label = CAT_LABELS.get(cat_id, "🛍 Другое")
        pct = round(amount / total * 100)
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        lines.append(f"{label}\n  {bar} {amount:,} тг ({pct}%)")

    await message.answer("\n".join(lines), parse_mode="HTML")