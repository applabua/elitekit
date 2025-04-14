import logging
import asyncio
from datetime import datetime
import nest_asyncio

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
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

# 🔐 Токен бота и ID админа
BOT_TOKEN = "8184346238:AAGe8YPi4MoT3kdWHWf-Ay1IwCMNlegFkAw"
ADMIN_ID = 2045410830

# 🔁 Состояния диалога
CHOOSING_SIZE, CHOOSING_QUANTITY, ENTER_LOCATION, ENTER_PHONE, CONFIRM_ORDER, WAIT_CONFIRMATION = range(6)

# 🖼️ Фото (прямые ссылки на изображения) – удалена картинка: https://i.ibb.co/SXxC7yK9/LACOSTE-2.png
PHOTOS = [
    "https://i.ibb.co/Kjr4hxKF/LACOSTE-5.png",
    "https://i.ibb.co/9k2R8sp5/LACOSTE-4.png",
    "https://i.ibb.co/spVJwPsg/LACOSTE-3.png",
    "https://i.ibb.co/XZhmp1ff/LACOSTE-1.png",
    "https://i.ibb.co/JwgVgV2D/LACOSTE.png",
]

# 📏 Доступные размеры
SIZES = ["S", "M", "L", "XL", "XXL", "XXXL"]

# 👋 Команда /start — отправка фотоальбома, описания и кнопки "Замовити"
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Сбрасываем данные пользователя, чтобы избежать залипания предыдущих состояний
    context.user_data.clear()
    user = update.effective_user
    username = user.username or "немає ніка"
    user_id = user.id
    logging.info(f"🔔 Користувач: {username} ({user_id}) запустив бота")
    
    # Отправляем фотоальбом
    media = [InputMediaPhoto(media=url) for url in PHOTOS]
    await update.message.reply_media_group(media=media)
    
    # Описание футболки
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

# 🛍️ Начало процесса заказа — выбор размера
async def order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Сбрасываем данные, если пользователь начинает новый заказ
    context.user_data.clear()
    await update.callback_query.answer()
    keyboard = [[InlineKeyboardButton(size, callback_data=size)] for size in SIZES]
    await update.callback_query.message.reply_text(
        text="Оберіть розмір:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_SIZE

# 📦 Получаем выбранный размер
async def size_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["size"] = update.callback_query.data
    await update.callback_query.message.reply_text(text="Введіть кількість футболок:")
    return CHOOSING_QUANTITY

# Ввод количества
async def quantity_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["quantity"] = update.message.text
    await update.message.reply_text(
        text="Введіть область, місто та відділення Нової Пошти або Укрпошти:"
    )
    return ENTER_LOCATION

# Ввод адреса доставки
async def location_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["location"] = update.message.text
    await update.message.reply_text(text="Введіть номер телефону:")
    return ENTER_PHONE

# Ввод номера телефона
async def phone_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    await update.message.reply_text(text="Введіть ваше ім'я:")
    return CONFIRM_ORDER

# Ввод имени и вывод сводки заказа с кнопками подтверждения/отмены
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
    return WAIT_CONFIRMATION

# ☑️ Обработка подтверждения заказа — отправка уведомления админу
async def confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
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

# ❌ Обработка отмены заказа
async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(text="❌ Замовлення скасовано.")
    return ConversationHandler.END

# 🚀 Главная функция запуска
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
            WAIT_CONFIRMATION: [CallbackQueryHandler(confirm_callback, pattern="^confirm$"),
                                 CallbackQueryHandler(cancel_callback, pattern="^cancel$")]
        },
        fallbacks=[CommandHandler("cancel", cancel_callback)],
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    
    print("Бот запущено 🟢")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
