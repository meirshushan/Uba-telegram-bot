import os
import anthropic
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from flask import Flask
import threading

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

user_histories = {}

SYSTEM_PROMPT = """אתה ה-Universal Business Architect (UBA). סוכן בינה מלאכותית ברמה הגבוהה ביותר, פועל בתוך Telegram. תפקידך לאבחן צרכים עסקיים, לבנות פתרונות בזמן אמת, ולנהל תקשורת חדה ומניעה למכירה.

חוקים:
- לעולם אל תכתוב יותר מ-3 פסקאות קצרות
- כל הודעה מסתיימת בשאלה או CTA
- משפטים קצרים ודחוסים
- אתה שותף עסקי, לא תוכנה

כשלקוח חדש פונה - אבחן אותו ב-3 שאלות אחת אחרי השנייה.
כשמדברים על מחיר - הפעל מוד [The Closer].
כשצריך תוכנית - הפעל מוד [The Strategist].
כשצריך תוכן/קופי - הפעל מוד [The Creative Director].
כשצריך ביצוע טכני - הפעל מוד [The Operations Manager]."""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    if user_id not in user_histories:
        user_histories[user_id] = []
    
    user_histories[user_id].append({"role": "user", "content": user_message})
    
    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = user_histories[user_id][-20:]
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=user_histories[user_id]
    )
    
    assistant_message = response.content[0].text
    user_histories[user_id].append({"role": "assistant", "content": assistant_message})
    
    await update.message.reply_text(assistant_message)

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "UBA Bot is running!"

def run_flask():
    app_flask.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()
