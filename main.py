import logging
from uuid import uuid4

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, InlineQueryHandler

import exceptions
from services.downloader.utils import AudioDownloader

from settings import ACCESS_TOKEN
from settings import ADMIN_ID

import os

from services.database.manager import DBManager

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)

db_manager = DBManager()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
    🎵 YouTube Audio Downloader Bot

    This Telegram bot allows you to download audio from YouTube videos. Simply send the bot a valid YouTube link, and it will extract the audio for you. Here are the available commands:

    1. /start: Begin interacting with the bot.
    2. /register <email> <password>: Register your Google account with an email and password.
    3. /reset: Reset your account settings.
    4. Send a valid YouTube link to receive the audio.

    Enjoy your favorite tunes! 🎧

    Security Note: To ensure safe storage of passwords, we use the Python cryptography library, specifically the Advanced Encryption Standard (AES) algorithm. So, you can trust us with your credentials.
    """
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    input = str(update.message.text).split(' ')
    
    if len(input) != 3:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid input, try again.")
        return
    
    account = {
        'username':input[1],
        'password':input[2]
    }

    try:
        db_manager.register(update.effective_chat.id, account)
    except exceptions.DatabaseRegisterError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You've already registered.")
    except exceptions.SQLiteError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Something went wrong.")
    else:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        text = """
        Account registered successfully. You're ready to start downloading!
        """
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        db_manager.delete(update.effective_chat.id)
    except exceptions.SQLiteError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Something went wrong.")
    else:
        text = """
        Account settings reset. You're ready to start again!
        """
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        account = db_manager.get_account(update.effective_chat.id)
        downloader = AudioDownloader(update.message.text, db_manager.get_account(update.effective_chat.id))
    except exceptions.DatabaseSelectError:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="⚠️ You need to register first. Use /register <email> <password>.")
    except exceptions.SQLiteError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Something went wrong.")

    except exceptions.InputError:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="❌ Invalid YouTube link. Please provide a valid one.")
    except exceptions.DownloadError:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="⚠️ This YouTube video is either unavailable or restricted. Please try another link.")
    except exceptions.LoginError:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="❌ Incorrect Google account login. Try reset and register again. ")
    else:
        await context.bot.send_audio(
            chat_id=update.effective_chat.id, 
            audio=open(downloader.filename,'rb'), 
            title=downloader.title,
        )
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        os.remove(downloader.filename)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (update.message.from_user.id != int(ADMIN_ID)):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You're not authorized to view this information.")
        return
    
    try:
        users_amount = db_manager.get_total_users()
    except exceptions.SQLiteError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Something went wrong.")
    else:
        text = f"""
        📊 Bot Statistics

        Total Users: {users_amount}
        Downloads after deploy : {AudioDownloader.download_count}
        """
        
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

def main() -> None:
    application = ApplicationBuilder().token(ACCESS_TOKEN).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    register_handler = CommandHandler('register', register, has_args=True)
    application.add_handler(register_handler)

    reset_handler = CommandHandler('reset', reset)
    application.add_handler(reset_handler)

    download_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), download)
    application.add_handler(download_handler)

    stats_handler = CommandHandler('stats', stats)
    application.add_handler(stats_handler)

    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    application.run_polling()


if __name__ == '__main__':
    main()
