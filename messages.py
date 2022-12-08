import logging

from telegram import Update
from telegram.ext import CallbackContext, ContextTypes, JobQueue

from config import CHANNEL, FOOTER


async def append_footer_text(update: Update, _: ContextTypes.DEFAULT_TYPE):
    print(f"append footer text :: {update}")

    await update.channel_post.edit_text(update.channel_post.text_html_urled + FOOTER)


async def append_footer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"append footer :: {update}")

    mg = update.channel_post.media_group_id
    original_caption = update.channel_post.caption_html_urled

    # it's a single message, not an album - hence does not contain a mediagroup_id
    if mg is None:

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
        if context.job_queue is not None:
            for job in context.job_queue.get_jobs_by_name(mg):
                logging.info(f"Removed job {job}")

                for post_id in job.data["ids"]:
                    prev_list.add(post_id)

                if job.data["text"] is not None:
                    original_caption = job.data["text"]

                job.schedule_removal()

        data = {"ids": prev_list}

        if original_caption is not None:
            data["text"] = original_caption

        # 10 seconds is maybe too high, but better waiting than achieving incorrect results because it may take longer
        context.job_queue.run_once(append_footer_mg, 10, data, mg)


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
