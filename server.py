# server.py — keeps the bot alive 24/7 on Render
from flask import Flask
from threading import Thread
import os
import asyncio
import nest_asyncio
from bot import main   # import the main() function from bot.py

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 MCQ Bot is running on Render!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

def run_bot():
    nest_asyncio.apply()
    asyncio.run(main())

if __name__ == "__main__":
    Thread(target=run_flask).start()
    run_bot()
