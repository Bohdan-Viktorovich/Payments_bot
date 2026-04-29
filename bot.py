import logging
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

# ─── CONFIG ───────────────────────────────────────────────
BOT_TOKEN = "8610811784:AAG9sSwuUzU-TiAugfWpbC7OVSTgzLeQwfA"
ADMIN_ID = 7262437300
MAIB_CARD = "5397 0200 6598 8634"
PRICE = 9  # USD

PRODUCTS = {
    "checklist": {
        "name": "✅ Client Onboarding Checklist",
        "desc": "25 action items • 5 phases • готов к работе сразу",
        "file_id": "BQACAgIAAxkBAAMFafHpssvQadE8XgABDIzkYfvKQN4BAAJglAACytiRS1hOPCnneqvmOwQ",
    },
    "calculator": {
        "name": "💰 Freelance Rate Calculator",
        "desc": "3 шага • формула расчёта ставки • перестань занижать цены",
        "file_id": "BQACAgIAAxkBAAMGafHpsqvG0f6GtmT0Ddf2Av0wDbkAAmGUAALK2JFL0cPNzHQR0HU7BA",
    },
    "bundle": {
        "name": "🎁 Оба чек-листа",
        "desc": "Client Onboarding + Rate Calculator — полный пакет",
        "file_id": None,  # отправляем оба файла
    },
}

BUNDLE_PRICE = 15  # скидка при покупке обоих

# ─── LOGGING ──────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ─── KEYBOARDS ────────────────────────────────────────────
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Client Onboarding Checklist — $9", callback_data="buy_checklist")],
        [InlineKeyboardButton(text="💰 Freelance Rate Calculator — $9", callback_data="buy_calculator")],
        [InlineKeyboardButton(text="🎁 Оба файла — $15 (скидка)", callback_data="buy_bundle")],
    ])

def confirm_keyboard(product_key: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил — отправить файл", callback_data=f"paid_{product_key}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")],
    ])

def admin_keyboard(user_id: int, product_key: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить файл", callback_data=f"send_{user_id}_{product_key}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{user_id}")],
    ])

# ─── HANDLERS ─────────────────────────────────────────────
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 Привет! Здесь ты можешь купить профессиональные чек-листы для фрилансеров.\n\n"
        "Выбери что тебя интересует:",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выбери что тебя интересует:",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data.startswith("buy_"))
async def buy_product(callback: CallbackQuery):
    product_key = callback.data.replace("buy_", "")
    product = PRODUCTS[product_key]
    price = BUNDLE_PRICE if product_key == "bundle" else PRICE

    await callback.message.edit_text(
        f"📄 *{product['name']}*\n"
        f"{product['desc']}\n\n"
        f"💵 Цена: *${price}*\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💳 *Оплата на карту MAIB:*\n"
        f"`{MAIB_CARD}`\n\n"
        f"После оплаты нажми кнопку ниже — я проверю и отправлю файл.",
        parse_mode="Markdown",
        reply_markup=confirm_keyboard(product_key)
    )

@dp.callback_query(F.data.startswith("paid_"))
async def paid(callback: CallbackQuery):
    product_key = callback.data.replace("paid_", "")
    product = PRODUCTS[product_key]
    price = BUNDLE_PRICE if product_key == "bundle" else PRICE
    user = callback.from_user

    # Уведомление админу
    await bot.send_message(
        ADMIN_ID,
        f"💰 *Новая оплата!*\n\n"
        f"👤 Пользователь: [{user.first_name}](tg://user?id={user.id})\n"
        f"🆔 ID: `{user.id}`\n"
        f"📄 Товар: {product['name']}\n"
        f"💵 Сумма: ${price}\n\n"
        f"Проверь оплату и отправь файл:",
        parse_mode="Markdown",
        reply_markup=admin_keyboard(user.id, product_key)
    )

    await callback.message.edit_text(
        "⏳ Отлично! Запрос отправлен.\n\n"
        "Я проверю оплату и пришлю файл в течение нескольких минут. "
        "Если что-то пойдёт не так — напиши @BohdanViktorovich1"
    )

# ─── ADMIN: ОТПРАВИТЬ ФАЙЛ ────────────────────────────────
@dp.callback_query(F.data.startswith("send_"))
async def send_file(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    parts = callback.data.split("_")
    user_id = int(parts[1])
    product_key = parts[2]
    product = PRODUCTS[product_key]

    try:
        if product_key == "bundle":
            # Отправляем оба файла
            await bot.send_document(user_id, PRODUCTS["checklist"]["file_id"],
                caption="✅ Client Onboarding Checklist\n\nСпасибо за покупку! 🙏")
            await bot.send_document(user_id, PRODUCTS["calculator"]["file_id"],
                caption="💰 Freelance Rate Calculator\n\nУдачи в работе! 🚀")
        else:
            await bot.send_document(
                user_id,
                product["file_id"],
                caption=f"📄 {product['name']}\n\nСпасибо за покупку! Удачи 🚀"
            )

        await callback.message.edit_text(
            f"✅ Файл отправлен пользователю `{user_id}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при отправке: {e}")

# ─── ADMIN: ОТКЛОНИТЬ ─────────────────────────────────────
@dp.callback_query(F.data.startswith("reject_"))
async def reject(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    user_id = int(callback.data.replace("reject_", ""))

    await bot.send_message(
        user_id,
        "❌ Оплата не найдена.\n\n"
        "Пожалуйста проверь что перевод прошёл и напиши @BohdanViktorovich1 — разберёмся!"
    )
    await callback.message.edit_text(f"❌ Пользователь `{user_id}` получил отказ.", parse_mode="Markdown")

# ─── RUN ──────────────────────────────────────────────────
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
