import asyncio
import datetime
import json
from itertools import islice
from typing import Dict

import cairosvg
import httpx
from telegram import Update
from telegram.ext import ContextTypes, CallbackContext

import config

LOSS_DESCRIPTIONS = {
    'tanks': "Panzer",
    'apv': "Gepanzerte Fahrzeuge",
    'artillery': "Artilleriesysteme",
    'mlrs': "Mehrfachraketenwerfer",
    'aaws': "Luftverteidigungssysteme",
    'aircraft': "Flugzeuge",
    'helicopters': "Hubschrauber",
    'uav': "Drohnen",
    'vehicles': "Lastkraftwägen",
    'boats': "Schiffe",
    'se': "Spezialausrüstung",
    'missiles': "Marschflugkörper",
    'personnel': "Personal"
}


def get_time() -> str:
    return (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y.%m.%d")


def chunks(data, size):
    it = iter(data)
    for i in range(0, len(data), size):
        yield {k: data[k] for k in islice(it, size)}


def format_number(number: int):
    return f"{number:,}".replace(",", ".")


def create_svg(total_losses: Dict[str, int], new_losses: Dict[str, int]):
    field_size = 3

    all_width = 1580

    margin = 24
    stroke_width = 2
    #  print("border_distance", border_distance)

    heading_size = 42
    heading_space = margin * 2.25 + heading_size

    items = list(chunks(total_losses, field_size))
    row_count = len(items)

    width_cell = (all_width - (field_size + 1) * margin) / (field_size)
    height_cell = 160

    all_height = row_count * height_cell + (row_count) * margin + heading_space

    now = (datetime.datetime.now() - datetime.timedelta(days=1))

    day = (now.date() - datetime.date(2022, 2, 24)).days

    svg = f"""<?xml version='1.0' encoding='UTF-8' standalone='no'?>
    <svg
       width='{all_width}'
       height='{all_height}'
       viewBox='0 0 {all_width} {all_height}'
       version='1.1'
       xmlns='http://www.w3.org/2000/svg'
       xmlns:svg='http://www.w3.org/2000/svg'>
    <text y="{heading_size + margin}" x="50%" font-size="{heading_size}"  font-family="Bahnschrift"  fill="lightgray"  ><tspan dy="0" x="50%"  text-anchor="middle"  >Russische Verluste in der Ukraine - Tag {day}</tspan></text>
    """

    #  print("------")

    for y, item in enumerate(items):
        #  print("items :: ", item)

        for x, (k, v) in enumerate(item.items()):
            #   print(y, x, "--", k, v)

            svg += f"""
        <rect width='{width_cell}' height='{height_cell}' x='{x * width_cell + (x + 1) * margin}'
         y="{(y * height_cell) + y * margin + heading_space}"  stroke="#2c5a2b" stroke-width="{stroke_width}" paint-order="fill" fill="#002a24"  />

<text x="{x * width_cell + (x + 2) * margin}" y="{(y * height_cell) + (y + 2) * margin + heading_space + stroke_width}" text-anchor="start" font-size="50px" font-family="Bahnschrift"  fill="white" dominant-baseline="central"  >
{format_number(v)}<tspan 
"""

            if new_losses[k] != 0:
                svg += f"""
                fill="#ffcc00"   > +{format_number(new_losses[k])}
            </tspan><tspan"""

            svg += f"""
  dy="1.5em" text-anchor="start" fill="#bedebd" x="{x * width_cell + (x + 2) * margin}" font-size="38px">{LOSS_DESCRIPTIONS[k]}</tspan>
</text>"""

    svg += f"""<text y="{all_height - margin - height_cell / 2}"  font-size="32px"  dominant-baseline="center" font-family="Bahnschrift"  text-anchor="end" fill="lightgray" >
               <tspan x="{all_width - margin}">Geschätzte Verluste vom 24.02.2022 bis {now.strftime("%d.%m.%Y")}</tspan>
               <tspan x="{all_width - margin}" dy="1.2em">Quelle: Ukrainisches Verteidigungsministerium</tspan>
               <tspan x="{all_width - margin}" dy="-2.4em" >Abonniere uns auf Telegram: @invasion_ukraine</tspan>
               </text>
</svg>"""

    print(svg)

    cairosvg.svg2png(bytestring=svg, write_to='field.png', background_color="#00231e")


async def get_api(context: CallbackContext):
    key = context.bot_data.get("last_loss", "")
    now = get_time()
    print("crawl: ", key, now)

    print(">>>> waiting... ", datetime.datetime.now().strftime("%d.%m.%Y, %H:%M:%S"), "::", key, "::", now)

    if key != now:
        print("---- requesting ---- ")

        res = httpx.get('https://russian-casualties.in.ua/api/v1/data/json/daily')
        data = json.load(res)["data"]
        #  print(data)

        try:
            new_losses = data[now]
            # new_losses.pop("captive")

        except KeyError as e:
            print("Could not get entry with key: ", e)
            return

        total_losses = {
            'personnel': 0,
            'tanks': 0,
            'apv': 0,
            'artillery': 0,
            'mlrs': 0,
            'aaws': 0,
            'aircraft': 0,
            'helicopters': 0,
            'vehicles': 0,
            'boats': 0,
            'se': 0,
            'uav': 0,
            'missiles': 0,
        }

        for day, item in data.items():
            print(day)

            for k, v in item.items():
                print(k, v)

                if k != "captive":
                    total_losses[k] = total_losses[k] + v

        print("---- found ---- ", datetime.datetime.now().strftime("%d.%m.%Y, %H:%M:%S"))

        create_svg(total_losses, new_losses)

        display_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%d.%m.%Y")
        text = f"🔥 <u>Russische Verluste bis zum {display_date}</u>\n\n"
        for k, v in total_losses.items():
            text += f"• {LOSS_DESCRIPTIONS[k]}: {v}\n"

        last_id = context.bot_data.get("last_loss_id", 1)

        text += f"\n🔗 <a href='https://t.me/invasion_ukraine/{last_id}'>vorige Statistik</a>{config.FOOTER}"

        print(text)

        with open("field.png", "rb") as f:
            msg = await context.bot.send_photo(config.CHANNEL, photo=f, caption=text)

        context.bot_data["last_loss"] = now
        context.bot_data["last_loss_id"] = msg.id


async def setup_crawl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("setup crwal")
    # del context.bot_data["last_loss"]
    await get_api(context)
    print("help?")
    context.job_queue.run_repeating(get_api, datetime.timedelta(hours=2))
    await update.message.reply_text("Scheduled Api Crawler.")
