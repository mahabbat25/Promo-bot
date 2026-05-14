import asyncio
import random
import string
import aiosqlite
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
DB_FILE = "promo_bot.db"
PROMO_PREFIX = "frnd_"
PROMO_LENGTH = 6

async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                promo_code TEXT,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def get_user_promo(user_id):
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT promo_code FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def save_user_promo(user_id, username, promo):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT INTO users (user_id, username, promo_code) VALUES (?, ?, ?)",
            (user_id, username or "", promo)
        )
        await db.commit()

async def generate_unique_promo():
    async with aiosqlite.connect(DB_FILE) as db:
        while True:
            suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=PROMO_LENGTH))
            code = PROMO_PREFIX + suffix
            async with db.execute("SELECT 1 FROM users WHERE promo_code = ?", (code,)) as cursor:
                if not await cursor.fetchone():
                    return code

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    existing = await get_user_promo(user.id)
    if existing:
        text = "Privet, " + user.first_name + "! Tvoy promokod uzhe vydan:\n\n" + existing + "\n\nKazhdy polzovatel poluchaet tolko odin promokod."
        await update.message.reply_text(text)
    else:
        promo = await generate_unique_promo()
        await save_user_promo(user.id, user.username, promo)
        text = "Gotovo! Tvoy promokod:\n\n" + promo + "\n\nPromokod odnorazovy i privyazan tolko k tebe."
        await update.message.reply_text(text)

async def cmd_mypromo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    promo = await get_user_promo(update.effective_user.id)
    if promo:
        await update.message.reply_text("Tvoy promokod: " + promo)
    else:
        await update.message.reply_text("Promokoda net. Napishi /start chtoby poluchit!")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - poluchit promokod\n/mypromo - moy promokod\n/help - pomosh")

async def main():
    await init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("mypromo", cmd_mypromo))
    app.add_handler(CommandHandler("help", cmd_help))
    print("Bot started!")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
