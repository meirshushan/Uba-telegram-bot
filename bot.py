import os
import asyncio
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from aiohttp import web

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
PORT = int(os.environ.get("PORT", 8080))

user_histories = {}

SYSTEM_PROMPT = """אתה ה-Universal Business Architect (UBA). סוכן בינה מלאכותית ברמה הגבוהה ביותר, פועל בתוך Telegram. תפקידך לאבחן צרכים עסקיים, לבנות פתרונות בזמן אמת, ולנהל תקשורת חדה ומניעה למכירה.
חוקים: לעולם אל תכתוב יותר מ-3 פסקאות קצרות. כל הודעה מסתיימת בשאלה או CTA. משפטים קצרים ודחוסים. אתה שותף עסקי, לא תוכנה.
כשלקוח חדש פונה - אבחן אותו ב-3 שאלות אחת אחרי השנייה.
כשמדברים על מחיר - הפעל מוד [The Closer].
כשצריך תוכנית - הפעל מוד [The Strategist].
כשצריך תוכן - הפעל מוד [The Creative Director].
כשצריך ביצוע טכני - הפעל מוד [The Operations Manager]."""

def ask_claude(messages):
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-opus-4-5",
            "max_tokens": 1000,
            "system": SYSTEM_PROMPT,
            "messages": messages
        }
    )
    return response.json()["content"][0]["text"]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    if user_id not in user_histories:
        user_histories[user_id] = []
    user_histories[user_id].append({"role": "user", "content": user_message})
    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = user_histories[user_id][-20:]
    reply = ask_claude(user_histories[user_id])
    user_histories[user_id].append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply)

async def health(request):
    return web.Response(text="UBA Bot is running!")

async def main():
    app_web = web.Application()
    app_web.router.add_get('/', health)
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
