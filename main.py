from telegram.ext import Application
from config import BOT_TOKEN, PORT
from bot import setup_handlers
import asyncio

async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    setup_handlers(application)

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    print(f"Bot is running on port {PORT}")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
