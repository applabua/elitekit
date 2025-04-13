import logging
import asyncio
from datetime import datetime
import nest_asyncio

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

nest_asyncio.apply()
logging.basicConfig(level=logging.INFO)

# 🔐 Токен бота та ID адміна
BOT_TOKEN = "8184346238:AAGe8YPi4MoT3kdWHWf-Ay1IwCMNlegFkAw"
ADMIN_ID = 2045410830

# 🔁 Стани розмови
CHOOSING_SIZE, CHOOSING_QUANTITY, ENTER_LOCATION, ENTER_PHONE, CONFIRM_ORDER = range(5)

# 🖼️ Фото (переконайся, що це прямі URL для зображень)
PHOTOS = [
    "https://i.ibb.co/QHC7sfB/LACOSTE.png",
    "https://i.ibb.co/4MKZWXd/LACOSTE-1.png",
    "https://i.ibb.co/0yKXJfB/LACOSTE-2.png",
    "https://i.ibb.co/k8jPCj7/LACOSTE-3.png",
    "https://i.ibb.co/YZxP2MY/LACOSTE-4.png",
    "https://i.ibb.co/zfpvS9h/LACOSTE-5.png",
]

# 📏 Розміри
SIZES = ["S", "M", "L", "XL", "XXL", "XXXL"]

# 👋 Стартове повідомлення (команда /start)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username or "немає ніка"
    user_id = user.id
    logging.info(f"🔔 Користувач: {username} ({user_id}) запустив бота")
    
    # Надсилаємо фото
    for link in PHOTOS:
        await update.message.reply_photo(photo=link)
    
    # Опис футболки
    description = (
        "🫡 <b>Футболка-поло ЗСУ (Олива)</b>\n"
        "🔹 Виготовлена з дихаючої, гіпоалергенної тканини Lacoste Pike\n"
        "🔹 Ідеальна для щоденного носіння\n"
        "🔹 Зносостійка та легка\n"
        "🔹 Виготовлено в Україні 🇺🇦\n\n"
        "💰 <b>Ціна: 950 грн</b>\n"
        "⚠️ Приймаємо замовлення тільки після 100% оплати\n"
    )
    await update.message.reply_text(text=description, parse_mode="HTML")
    
    # Кнопка "Замовити"
    keyboard = [[InlineKeyboardButton("🛒 Замовити", callback_data="order")]]
    await update.message.reply_text(
        text="Натисніть нижче, щоб оформити замовлення:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return ConversationHandler.END

# 🛍️ Починаємо процес замовлення — вибір розміру
async def order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(size, callback_data=size)] for size in SIZES]
    await update.callback_query.message.reply_text(
        text="Оберіть розмір:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_SIZE

# 📦 Після вибору розміру, просимо ввести кількість
async def size_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["size"] = update.callback_query.data
    await update.callback_query.message.reply_text(text="Введіть кількість футболок:")
    return CHOOSING_QUANTITY

# 📍 Отримуємо інформацію про доставку
async def quantity_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["quantity"] = update.message.text
    await update.message.reply_text(
        text="Введіть область, місто та відділення Нової Пошти або Укрпошти:"
    )
    return ENTER_LOCATION

# 📱 Отримуємо номер телефону
async def location_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["location"] = update.message.text
    await update.message.reply_text(text="Введіть номер телефону:")
    return ENTER_PHONE

# 👤 Отримуємо ім'я клієнта для підтвердження замовлення
async def phone_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    await update.message.reply_text(text="Введіть ваше ім'я:")
    return CONFIRM_ORDER

# ✅ Фінальне підтвердження замовлення
async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    data = context.user_data
    
    summary = (
        f"🧾 <b>Ваше замовлення:</b>\n"
        f"👕 Розмір: {data['size']}\n"
        f"🔢 Кількість: {data['quantity']}\n"
        f"📍 Доставка: {data['location']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"👤 Ім'я: {data['name']}\n"
        f"💳 Оплата: 950 грн/шт\n\n"
        "Підтверджуєте замовлення?"
    )
    buttons = [
        [InlineKeyboardButton("✅ Підтвердити", callback_data="confirm")],
        [InlineKeyboardButton("❌ Скасувати", callback_data="cancel")]
    ]
    await update.message.reply_text(
        text=summary,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return ConversationHandler.END

# ☑️ Підтвердження замовлення — надсилаємо повідомлення адміну
async def confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = context.user_data
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = (
        f"🆕 НОВЕ ЗАМОВЛЕННЯ\n"
        f"👤 @{user.username} ({user.id})\n"
        f"⏰ {now} (за Києвом)\n\n"
        f"Розмір: {data['size']}\n"
        f"Кількість: {data['quantity']}\n"
        f"Доставка: {data['location']}\n"
        f"Телефон: {data['phone']}\n"
        f"Ім'я: {data['name']}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=message)
    
    await update.callback_query.message.reply_text(
        text="✅ Дякуємо! Ваше замовлення обробляється. Очікуйте на дзвінок 📞"
    )
    return ConversationHandler.END

# ❌ Скасування замовлення
async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text(text="❌ Замовлення скасовано.")
    return ConversationHandler.END

# 🚀 Головна функція запуску
async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(order_callback, pattern="^order$")],
        states={
            CHOOSING_SIZE: [CallbackQueryHandler(size_chosen)],
            CHOOSING_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, quantity_entered)],
            ENTER_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, location_entered)],
            ENTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_entered)],
            CONFIRM_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_order)],
        },
        fallbacks=[
            CallbackQueryHandler(confirm_callback, pattern="^confirm$"),
            CallbackQueryHandler(cancel_callback, pattern="^cancel$")
        ],
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    
    print("Бот запущено 🟢")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
