import datetime
import logging
import re
import time as t

from telegram import Update
from telegram.ext import CallbackContext, ContextTypes

import config
from config import CHANNEL, FOOTER


async def append_footer_text(update: Update, _: ContextTypes.DEFAULT_TYPE):
    print(f"append footer text :: {update}")

    text = update.channel_post.text_html_urled

    await update.channel_post.edit_text(text + FOOTER)


async def append_footer_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"append footer forward :: {update}")

    time = t.time()
    is_valid = update.channel_post.forward_from_chat.id == -1001839268196 and update.channel_post.media_group_id is None

    print(is_valid, time)
    print(datetime.datetime.now().timestamp(), context.bot_data.get("latest", time))

    if is_valid and time < context.bot_data.get("latest", time):
        text = re.sub(r"\s*$", "", re.sub(r"Quelle:(.|\s)*", "", update.channel_post.caption_html_urled)) + FOOTER
        await update.channel_post.copy(CHANNEL, text)
        # await update.channel_post.delete()
        print("-- delete -")

    else:
        context.bot_data["latest"] = time + 5400


async def append_footer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"append footer :: {update}")

    original_caption = update.channel_post.caption_html_urled

    # it's a single message, not an album - hence does not contain a mediagroup_id
    if update.channel_post.media_group_id is None:

        if original_caption is None:
            original_caption = ""

        try:
            await update.channel_post.edit_caption(original_caption + FOOTER)
        except Exception as e:
            logging.exception("Error editing single :: ", e)
            pass

    else:
        prev_list = {update.channel_post.id}

        # go through already present jobs and get their dat

        for job in context.job_queue.get_jobs_by_name(update.channel_post.media_group_id):
            logging.info(f"Removed job {job}")

            for post_id in job.data["ids"]:
                prev_list.add(post_id)

            if "text" in job.data:
                original_caption = job.data["text"]

                job.schedule_removal()

        data = {"ids": prev_list}

        if original_caption is not None:
            data["text"] = original_caption

        # 10 seconds is maybe too high, but better waiting than achieving incorrect results because it may take longer
        context.job_queue.run_once(append_footer_mg, 8, data, update.channel_post.media_group_id)


async def append_footer_mg(context: CallbackContext):
    print(f"append_footer_mg :: {context}")

    logging.info("job-data", context.job.data)
    posts = sorted(context.job.data["ids"])

    # clearing the caption for all posts other than the first one in this mediagroup.
    # because if two posts in a media contain a caption, there will be no caption showing up in preview,
    # you have to click through the entries of the album to see individual captions.
    for post in posts[1:]:
        try:
            await context.bot.edit_message_caption(CHANNEL, post, caption=None)
        except Exception as e:
            if e.message != "Message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message":
                logging.exception("Error editing mediagroup other :: ", e)
            pass

    try:
        await context.bot.edit_message_caption(CHANNEL, posts[0], caption=context.job.data["text"] + FOOTER)
    except Exception as e:
        logging.exception("Error editing mediagroup text :: ", e)
        pass


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("update::: ", update.message)

    await update.message.delete()

    if update.message.reply_to_message is not None:
        if update.message.reply_to_message.is_automatic_forward:
            text = f"💬  <a href='{update.message.reply_to_message.link}'>Kanalpost</a>"
            response = "Danke für deine Meldung, wir Admins prüfen das 😊"
        else:
            text = f"‼️ <a href='{update.message.reply_to_message.link}'>Nachricht</a> des Nutzers {update.message.reply_to_message.from_user.mention_html()}"
            response = "Ein Nutzer hat deine Nachricht gemeldet, wir Admins prüfen das. Bitte sei brav 😉"

        text += f" gemeldet von {update.message.from_user.mention_html()}:\n\n"

        if update.message.reply_to_message.caption is not None:
            text += update.message.reply_to_message.caption_html_urled
        else:
            text += update.message.reply_to_message.text_html_urled

        await context.bot.send_message(config.GROUP_ADMIN, text)

        await update.message.reply_to_message.reply_text(response)


def is_admin(update: Update):
    return update.message.reply_to_message is not None and (
                update.message.from_user.id in config.ADMINS or update.message.from_user.username == "GroupAnonymousBot") and update.message.reply_to_message.from_user.id not in config.ADMINS


async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.delete()

    if is_admin(update):
        warnings = context.bot_data.get(update.message.reply_to_message.from_user.id, 0) + 1

        if warnings <= config.MAX_WARNINGS:
            context.bot_data[update.message.reply_to_message.from_user.id] = warnings

            await update.message.reply_to_message.reply_text(
                f"‼️ <b>Für diese Nachricht wurdest du verwarnt!</b>\n\nDamit hast du {warnings} Warnungen. Bei {config.MAX_WARNINGS} fliegst du. Generell sind wir bei bereits verwarnten Nutzern strenger was diese Entscheidung betrifft.\n\nBitte verhalte dich zivilisiert, sei einfach brav und pöble nicht rum. Grundloser Hass und Trolle haben hier nichts verloren.")


async def unwarn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.delete()

    if is_admin(update):
        warnings = context.bot_data.get(update.message.reply_to_message.from_user.id, 1) - 1

        if warnings >= 0:
            context.bot_data[update.message.reply_to_message.from_user.id] = warnings

            await update.message.reply_to_message.reply_text(
                f"🎉 <b>Dir wurde eine Warnung erlassen! </b>\n\nDamit hast du {warnings} Warnungen. Bei {config.MAX_WARNINGS} fliegst du.")
