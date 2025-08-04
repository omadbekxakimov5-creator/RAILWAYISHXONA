import logging
import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# === TOKEN bu yerda bevosita yozilgan ===
BOT_TOKEN = "8200448854:AAGbmtFAxCdJENWUDzKh4R4Ch68lYKsuxII"  # bu yerga o'zingizning bot tokeningizni yozing

# Qo‘llab-quvvatlanadigan valyutalar
currencies = ['USD', 'EUR', 'RUB', 'GBP', 'JPY']

# State’lar
CHOOSING, TYPING_AMOUNT, CHOOSING_TARGET = range(3)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_exchange_rates():
    try:
        response = requests.get('https://cbu.uz/uz/arkhiv-kursov-valyut/json/')
        data = response.json()
        rates = {}
        for item in data:
            code = item['Ccy']
            if code in currencies:
                rates[code] = float(item['Rate'].replace(',', '.'))
        return rates
    except Exception as e:
        logging.error(f"Kurslarni olishda xatolik: {e}")
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['Hozirgi kurslar'], ['So‘mni boshqa valyutalarga o‘zgartirish']]
    await update.message.reply_text(
        "💸 Salom! Men valyuta kurslarini ko‘rsataman.\n"
        "Quyidagilardan birini tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    )
    return CHOOSING


async def choosing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == 'Hozirgi kurslar':
        rates = get_exchange_rates()
        if rates:
            msg = "📈 Hozirgi valyuta kurslari (so'mda):\n"
            for cur in currencies:
                msg += f"🔹 {cur}: {rates[cur]:,.2f} so'm\n"
            # YANGI: "Ortga" tugmasi qo‘shildi
            keyboard = [['🔙 Ortga']]
            await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
            return CHOOSING  # davom ettiradi
        else:
            await update.message.reply_text("❌ Kurslarni olishda muammo bo'ldi.", reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

    elif text == 'So‘mni boshqa valyutalarga o‘zgartirish':
        await update.message.reply_text("💰 Iltimos, so'mda miqdorni kiriting:", reply_markup=ReplyKeyboardRemove())
        return TYPING_AMOUNT

    elif text == '🔙 Ortga':
        return await start(update, context)  # boshlanishga qaytadi

    else:
        await update.message.reply_text("Menyudan tanlang.")
        return CHOOSING


async def typing_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit():
        await update.message.reply_text("❗ Iltimos, faqat raqam kiriting.")
        return TYPING_AMOUNT
    context.user_data['amount'] = int(text)

    keyboard = [[cur] for cur in currencies]
    await update.message.reply_text("🌍 Qaysi valyutaga aylantiray?", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return CHOOSING_TARGET


async def choosing_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.message.text
    if target not in currencies:
        await update.message.reply_text("❗ Noto‘g‘ri valyuta, ro‘yxatdan tanlang.")
        return CHOOSING_TARGET

    amount = context.user_data.get('amount')
    rates = get_exchange_rates()
    if not rates or target not in rates:
        await update.message.reply_text("❌ Kurslarni olishda muammo bo‘ldi.")
        return ConversationHandler.END

    converted = amount / rates[target]
    await update.message.reply_text(
        f"💱 {amount:,} so‘m = {converted:.2f} {target}", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❎ Bekor qilindi.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choosing)],
            TYPING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, typing_amount)],
            CHOOSING_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, choosing_target)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    print("✅ Bot ishga tushdi...")
    app.run_polling()


if __name__ == '__main__':
    main()
