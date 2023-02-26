import os
from dotenv import load_dotenv
load_dotenv()

# Railway and Heroku need that, to assign the proper webhook
PORT = os.getenv("PORT")

# This has to be the ID or public username of your channel
CHANNEL = -1001638826420
GROUP_ADMIN=-855684999
GROUP_CHAT=-1001631149964

# Replace it with whatever footer you want to append to your messages
FOOTER = "\n\nFolge uns für mehr!\n👉🏼 @invasion_ukraine 🇺🇦"

# if you test it locally, you can just do something like TOKEN="123abc--replace-this-with-what-@botfather-sent-you!"
TOKEN = os.getenv("TELEGRAM")

ADMINS = {
1732408088, #Nichda
703453307 #Nyx
}
MAX_WARNINGS = 3