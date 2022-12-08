import logging

from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, filters, Defaults
from telegram.ext import MessageHandler

from config import CHANNEL, TOKEN, TEST_MODE, PORT
from messages import append_footer, append_footer_text

logging.basicConfig(format="%(asctime)s -  %(levelname)s - [%(filename)s:%(lineno)s - %(funcName)20s()]: %(message)s ",
                    level=logging.INFO)


def main():
    app = ApplicationBuilder() \
        .token(TOKEN) \
        .defaults(Defaults(parse_mode=ParseMode.HTML, disable_web_page_preview=True)) \
        .build()

    # This filters for Photos, Videos and Gifs in your Channel. Normal Text-messages are ignored.
    app.add_handler(MessageHandler(
        (filters.PHOTO | filters.VIDEO | filters.ANIMATION) & filters.Chat(chat_id=CHANNEL) & ~filters.FORWARDED,
        append_footer))

    app.add_handler(
        MessageHandler(filters.TEXT & filters.Chat(chat_id=CHANNEL) & ~filters.FORWARDED, append_footer_text))

    if TEST_MODE:
        print("### Start Local ###")
        app.run_polling()
    else:
        # Replace the webhook_url with what Railway or Heroku give you
        app.run_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN,
                        webhook_url=f"https://web-production-fac5.up.railway.app/{TOKEN}")


if __name__ == '__main__':
    main()
