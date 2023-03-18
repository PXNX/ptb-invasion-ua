# import logging
import logging
import os
import re
from datetime import datetime

from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, filters, Defaults, CommandHandler, PicklePersistence
from telegram.ext import MessageHandler

import config
from config import CHANNEL, TOKEN
from crawl_api import setup_crawl
from messages import append_footer, append_footer_text, append_footer_forward, admin, warn, unwarn

LOG_FILENAME = rf"C:\Users\Pentex\PycharmProjects\ptb-invasion-ua\logs\{datetime.now().strftime('%Y-%m-%d')}\{datetime.now().strftime('%H-%M-%S')}.out"
os.makedirs(os.path.dirname(LOG_FILENAME), exist_ok=True)
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)s - %(funcName)20s()]: %(message)s ",
    level=logging.INFO, filename=LOG_FILENAME
)


def main():
    app = ApplicationBuilder() \
        .token(TOKEN) \
        .defaults(Defaults(parse_mode=ParseMode.HTML, disable_web_page_preview=True)) \
        .persistence(PicklePersistence(filepath="persistence")) \
        .build()

    app.add_handler(MessageHandler(filters.Chat(config.GROUPS) & filters.Regex(re.compile(r'^@admin', re.IGNORECASE)),
                                   admin))  # filters.Chat(chat_id=config.GROUP_CHAT) &

    # This filters for Photos, Videos and Gifs in your Channel. Normal Text-messages are ignored.
    app.add_handler(MessageHandler(
        filters.UpdateType.CHANNEL_POST & (filters.PHOTO | filters.VIDEO | filters.ANIMATION) & filters.Chat(
            chat_id=CHANNEL) & ~filters.FORWARDED, append_footer))

    app.add_handler(MessageHandler(
        filters.UpdateType.CHANNEL_POST & filters.TEXT & filters.Chat(chat_id=CHANNEL) & ~filters.FORWARDED,
        append_footer_text))

    app.add_handler(MessageHandler(
        filters.UpdateType.CHANNEL_POST & (filters.PHOTO | filters.VIDEO | filters.ANIMATION) & filters.Chat(
            chat_id=CHANNEL) & filters.FORWARDED,
        append_footer_forward))

    app.add_handler(CommandHandler("crawl", setup_crawl, filters.Chat(config.ADMINS)))
    app.add_handler(CommandHandler("warn", warn, filters.Chat(config.GROUPS)))
    app.add_handler(CommandHandler("unwarn", unwarn, filters.Chat(config.GROUPS)))

    print("### Start Local ###")
    app.run_polling()


if __name__ == '__main__':
    main()
