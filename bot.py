import asyncio
import os
import random
import re
import tempfile
from telegram import InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from extractor import extract_mcqs_from_pdf

BOT_TOKEN = "8482843522:AAF8cmJu6KgYt1j5vGt0n_vE1yKNFk4gPpw"

# Escape special characters for MarkdownV2
def esc_md2(text):
    return re.sub(r'([_\*\[\]\(\)~`>#+\-=|{}.!])', r'\\\1', text)

# Start command
async def start(update, ctx):
    await update.message.reply_text(
        "👋 Send me a Biochemistry PDF, and I’ll extract MCQs topic-wise with polls and explanations!"
    )

# Handle incoming PDFs
async def handle_pdf(update, ctx):
    file = await update.message.document.get_file()
    path = os.path.join(tempfile.gettempdir(), file.file_path.split('/')[-1])
    await file.download_to_drive(path)

    await update.message.reply_text("📄 Extracting MCQs topic-wise… Please wait ⏳")

    mcqs_by_topic = extract_mcqs_from_pdf(path)
    if not mcqs_by_topic:
        await update.message.reply_text("❌ No MCQs found in this PDF.")
        return

    # --- Topic-wise Poll Posting ---
    for topic, mcqs in mcqs_by_topic.items():
        header = f"📘 *Topic:* {esc_md2(topic)}"
        await ctx.bot.send_message(
            chat_id=update.effective_chat.id, text=header, parse_mode="MarkdownV2"
        )

        for i, m in enumerate(mcqs, start=1):
            q_text = f"🧠 Q{i}. {m['question']}"
            if len(q_text) > 280:
                q_text = q_text[:277] + "..."
            opts = [o[:95] + "…" if len(o) > 98 else o for o in m["options"]]

            # --- Send poll ---
            try:
                await ctx.bot.send_poll(
                    chat_id=update.effective_chat.id,
                    question=q_text,
                    options=opts,
                    type="quiz",
                    correct_option_id=m["correct_index"],
                    is_anonymous=False,
                )
            except Exception as e:
                await update.message.reply_text(f"⚠️ Skipped one MCQ: {e}")
                continue

            # --- Send related images ---
            for img_path in m["images"]:
                try:
                    with open(img_path, "rb") as img:
                        await ctx.bot.send_photo(
                            update.effective_chat.id, InputFile(img)
                        )
                except:
                    pass

            # --- Hidden Answer + Explanation ---
            if m["explanation"]:
                text_to_hide = (
                    f"✅ *Answer:* {opts[m['correct_index']]}\n\n🩺 *Explanation:* {m['explanation']}"
                )
                safe_text = esc_md2(text_to_hide)
                await ctx.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"||{safe_text}||",
                    parse_mode="MarkdownV2",
                )

            # --- Adaptive flood control delay ---
            delay = 3 + random.uniform(0.5, 1.5)
            if m.get("images") or m.get("explanation"):
                delay += 2
            await asyncio.sleep(delay)

        # Separator after each topic
        await ctx.bot.send_message(
            chat_id=update.effective_chat.id,
            text="—" * 20 + "\n🧩 End of Topic\n",
        )

        # Pause between topic batches
        await asyncio.sleep(20)

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    print("🤖 Bot is running (topic-wise MCQs)...")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio, asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
