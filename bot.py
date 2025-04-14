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

# =======================
#  Настройка логирования
# =======================
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# Скрываем лишние логи внутренних модулей
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

nest_asyncio.apply()

# 🔐 Токен бота и ID админа
BOT_TOKEN = "8184346238:AAGe8YPi4MoT3kdWHWf-Ay1IwCMNlegFkAw"
ADMIN_ID = 2045410830

# 🔁 Состояния диалога
CHOOSING_SIZE, CHOOSING_QUANTITY, ENTER_LOCATION, ENTER_PHONE, CONFIRM_ORDER, WAIT_CONFIRMATION = range(6)

# 🖼️ Ссылки на КВАЛИТЕТНЫЕ изображения  
# Добавлен параметр ?quality=100 (если поддерживается сервером) и исключена одна картинка
PHOTOS = [
    "https://i.ibb.co/Kjr4hxKF/LACOSTE-5.png?quality=100",
    "https://i.ibb.co/9k2R8sp5/LACOSTE-4.png?quality=100",
    "https://i.ibb.co/spVJwPsg/LACOSTE-3.png?quality=100",
    "https://i.ibb.co/XZhmp1ff/LACOSTE-1.png?quality=100",
    "https://i.ibb.co/JwgVgV2D/LACOSTE.png?quality=100",
]

# 📏 Доступные размеры
SIZES = ["S", "M", "L", "XL", "XXL", "XXXL"]

# ===========================
#       ОБРАБОТЧИКИ БОТА
# ===========================

# /start — отправка фотоальбома, краткого описания и кнопки "Замовити"
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    
    user = update.effective_user
    username = user.username or "немає ніка"
    user_id = user.id
    logging.info(f"Пользователь @{username} ({user_id}) запустил бота.")
    
    # Отправляем фотоальбом
    media = [InputMediaPhoto(media=url) for url in PHOTOS]
    await update.message.reply_media_group(media=media)
    
    # Краткое, но ёмкое описание товара с переносами строк,
    # чтобы текст не был слишком большим и не растягивался по ширине.
    description = (
        "🫡 <b>Футболка-поло ЗСУ (Олива)</b>\n"
        "(Статутного зразку)\n"
        "Вироблена з високоякісного матеріалу,\n"
        "що гарантує комфорт та зносостійкість.\n"
        "🔹 <i>Тканина Lacoste:</i> дихаюча, гіпоалергенна\n"
        "🔹 Ідеальна для щоденного носіння\n"
        "🔹 Легка та зручна\n"
        "🔹 Зносостійка\n"
        "🔹 Вироблено в Україні 🇺🇦\n\n"
        "💰 <b>Ціна: 950 грн/шт</b>\n"
        "⚠️ Приймаємо замовлення лише після\n"
        "   100% передоплати."
    )
    await update.message.reply_text(text=description, parse_mode="HTML")
    
    # Кнопка "Замовити"
    keyboard = [[InlineKeyboardButton("🛒 Замовити", callback_data="order")]]
    await update.message.reply_text(
        text="Натисніть, щоб зробити замовлення:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return ConversationHandler.END

# Начало процесса заказа — выбор размера
async def order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.callback_query.answer()
    
    user = update.effective_user
    username = user.username or "немає ніка"
    user_id = user.id
    logging.info(f"Пользователь @{username} ({user_id}) нажал кнопку 'Замовити'.")
    
    # Выводим варианты размеров
    keyboard = [[InlineKeyboardButton(size, callback_data=size)] for size in SIZES]
    await update.callback_query.message.reply_text(
        text="Оберіть розмір:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_SIZE

# Получаем выбранный размер
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
        "🧾 <b>Ваше замовлення:</b>\n"
        f"👕 Розмір: {data['size']}\n"
        f"🔢 Кількість: {data['quantity']}\n"
        f"📍 Доставка: {data['location']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"👤 Ім'я: {data['name']}\n"
        "💳 Оплата: 950 грн/шт\n\n"
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

# Обработка подтверждения заказа — отправка уведомления админу
async def confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user = update.effective_user
    username = user.username or "немає ніка"
    user_id = user.id
    data = context.user_data
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = (
        "🆕 НОВЕ ЗАМОВЛЕННЯ\n"
        f"👤 @{username} ({user_id})\n"
        f"⏰ {now} (за Києвом)\n\n"
        f"Розмір: {data['size']}\n"
        f"Кількість: {data['quantity']}\n"
        f"Доставка: {data['location']}\n"
        f"Телефон: {data['phone']}\n"
        f"Ім'я: {data['name']}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=message)
    
    logging.info(
        f"Пользователь @{username} ({user_id}) підтвердив заказ: "
        f"size={data['size']}, quantity={data['quantity']}, location={data['location']}"
    )
    
    await update.callback_query.message.reply_text(
        text="✅ Дякуємо! Ваше замовлення обробляється. Очікуйте на дзвінок 📞"
    )
    return ConversationHandler.END

# Обработка отмены заказа
async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user = update.effective_user
    username = user.username or "немає ніка"
    user_id = user.id
    logging.info(f"Пользователь @{username} ({user_id}) скасував замовлення.")
    
    await update.callback_query.message.reply_text(text="❌ Замовлення скасовано.")
    return ConversationHandler.END

# ===========================
#     ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА
# ===========================
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
            WAIT_CONFIRMATION: [
                CallbackQueryHandler(confirm_callback, pattern="^confirm$"),
                CallbackQueryHandler(cancel_callback, pattern="^cancel$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_callback)],
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    
    print("Бот запущен 🟢")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
