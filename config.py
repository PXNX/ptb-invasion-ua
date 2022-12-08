import os
from dotenv import load_dotenv
load_dotenv()

# Railway and Heroku need that, to assign the proper webhook
PORT = os.getenv("PORT")

# This has to be the ID or public username of your channel
CHANNEL = -1001638826420

# Replace it with whatever footer you want to append to your messages
FOOTER = "\n\nFolge uns für mehr!\n👉🏼 <a href='https://t.me/invasion_ukraine'>Invasion Ukraine 🇺🇦</a>"

# if you test it locally, you can just do something like TOKEN="123abc--replace-this-with-what-@botfather-sent-you!"
TOKEN = os.getenv("TELEGRAM")

TEST_MODE = True