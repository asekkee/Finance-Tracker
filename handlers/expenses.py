import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database import save_expense

router = Router()

CATEGORIES = {
    "food":      "🍔 Еда",
    "fun":       "🎮 Развлечения",
    "transport": "🚕 Транспорт",
    "books":     "📚 Книги",
    "invest":    "📈 Инвестиции",
    "other":     "🛍 Другое",
}

# Храним временно расходы без категории: { user_id: [ {amount, description}, ... ] }
pending: dict[int, list[dict]] = {}


def parse_lines(text: str) -> list[dict]:
    """Парсит каждую строку вида '200 вода'. Возвращает список найденных расходов."""
    result = []
    for line in text.strip().splitlines():
        line = line.strip()
        match = re.match(r"^(\d+)\s+(.+)", line)
        if match:
            result.append({
                "amount": int(match.group(1)),
                "description": match.group(2).strip(),
            })
    return result


def build_category_keyboard(index: int, amount: int, description: str) -> InlineKeyboardMarkup:
    """Кнопки категорий для одного расхода. index — порядковый номер в очереди."""
    buttons = []
    for cat_id, cat_label in CATEGORIES.items():
        short_desc = description[:25].replace("|", "")
        buttons.append(
            InlineKeyboardButton(
                text=cat_label,
                callback_data=f"cat|{index}|{cat_id}|{amount}|{short_desc}",
            )
        )
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def ask_next_category(message: Message, user_id: int):
    """Спрашивает категорию для следующего расхода в очереди."""
    queue = pending.get(user_id, [])
    if not queue:
        return

    item = queue[0]  # берём первый из очереди
    index = 0
    keyboard = build_category_keyboard(index, item["amount"], item["description"])

    remaining = len(queue)
    counter = f"<i>({remaining} осталось)</i> " if remaining > 1 else ""

    await message.answer(
        f"{counter}💳 <b>{item['amount']:,} тг</b> — {item['description']}\n\nВыберите категорию:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


# ─── Обработчик входящих сообщений ───────────────────────────────────────────

@router.message(F.text.regexp(r"(?m)^\d+\s+\S"))
async def handle_expense(message: Message):
    """Ловит одну или несколько строк вида '200 вода'."""
    items = parse_lines(message.text)
    if not items:
        return

    user_id = message.from_user.id

    if len(items) == 1:
        # Один расход — просто спрашиваем категорию
        pending[user_id] = items
        await ask_next_category(message, user_id)

    else:
        # Несколько расходов — показываем что получили и начинаем по очереди
        pending[user_id] = items
        lines = "\n".join(f"  • {i['amount']:,} тг — {i['description']}" for i in items)
        await message.answer(
            f"📋 Получил <b>{len(items)} расхода(ов)</b>:\n{lines}\n\n"
            f"Сейчас выберем категорию для каждого 👇",
            parse_mode="HTML",
        )
        await ask_next_category(message, user_id)


# ─── Обработчик нажатия на категорию ─────────────────────────────────────────

@router.callback_query(F.data.startswith("cat|"))
async def handle_category(callback: CallbackQuery):
    """Сохраняет расход и переходит к следующему в очереди."""
    parts = callback.data.split("|", 4)
    # формат: cat | index | cat_id | amount | description
    _, index_str, cat_id, amount_str, description = parts
    amount = int(amount_str)
    cat_label = CATEGORIES.get(cat_id, "🛍 Другое")
    user_id = callback.from_user.id

    save_expense(
        user_id=user_id,
        amount=amount,
        category=cat_id,
        description=description,
    )

    # Убираем сохранённый расход из очереди
    queue = pending.get(user_id, [])
    if queue:
        queue.pop(0)

    await callback.message.edit_text(
        f"✅ <b>{amount:,} тг</b> — {cat_label} · {description}",
        parse_mode="HTML",
    )
    await callback.answer()

    # Если в очереди ещё есть расходы — спрашиваем следующий
    if queue:
        await ask_next_category(callback.message, user_id)
    else:
        # Вся очередь обработана
        pending.pop(user_id, None)
        await callback.message.answer("🎉 Все расходы сохранены! Посмотреть: /today")