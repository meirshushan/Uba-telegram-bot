import os
import requests
import time

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

user_histories = {}

SYSTEM_PROMPT = """אתה ה-Universal Business Architect (UBA). סוכן בינה מלאכותית ברמה הגבוהה ביותר. תפקידך לאבחן צרכים עסקיים ולנהל תקשורת חדה ומניעה למכירה.
חוקים: לא יותר מ-3 פסקאות. כל הודעה מסתיימת בשאלה. משפטים קצרים. אתה שותף עסקי.
כשלקוח חדש פונה - שאל 3 שאלות אחת אחרי השנייה.
כשמדברים על מחיר - [The Closer]. כשצריך תוכנית - [The Strategist]. כשצריך תוכן - [The Creative Director]."""

def send_message(chat_id, text):
    requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text})

def ask_claude(messages):
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-opus-4-5", "max_tokens": 1000, "system": SYSTEM_PROMPT, "messages": messages}
    )
    return r.json()["content"][0]["text"]

def main():
    offset = 0
    print("Bot started!")
    while True:
        try:
            r = requests.get(f"{BASE_URL}/getUpdates", params={"offset": offset, "timeout": 30}, timeout=35)
            updates = r.json().get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                text = msg.get("text", "")
                chat_id = msg.get("chat", {}).get("id")
                if not text or not chat_id or text.startswith("/"):
                    continue
                if chat_id not in user_histories:
                    user_histories[chat_id] = []
                user_histories[chat_id].append({"role": "user", "content": text})
                if len(user_histories[chat_id]) > 20:
                    user_histories[chat_id] = user_histories[chat_id][-20:]
                reply = ask_claude(user_histories[chat_id])
                user_histories[chat_id].append({"role": "assistant", "content": reply})
                send_message(chat_id, reply)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
