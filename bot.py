import os, requests, time, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
PORT = int(os.environ.get("PORT", 8080))
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
user_histories = {}
SYSTEM_PROMPT = """אתה ה-UBA. סוכן עסקי חד ומהיר. לא יותר מ-3 פסקאות. כל הודעה מסתיימת בשאלה. כשלקוח חדש פונה - שאל 3 שאלות אחת אחרי השנייה."""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        pass

def send_msg(chat_id, text):
    requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text})

def ask_claude(msgs):
    r = requests.post("https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-opus-4-5", "max_tokens": 1000, "system": SYSTEM_PROMPT, "messages": msgs})
    return r.json()["content"][0]["text"]

def bot_loop():
    offset = 0
    while True:
        try:
            r = requests.get(f"{BASE_URL}/getUpdates", params={"offset": offset, "timeout": 30}, timeout=35)
            for u in r.json().get("result", []):
                offset = u["update_id"] + 1
                msg = u.get("message", {})
                text = msg.get("text", "")
                chat_id = msg.get("chat", {}).get("id")
                if not text or not chat_id or text.startswith("/"): continue
                if chat_id not in user_histories: user_histories[chat_id] = []
                user_histories[chat_id].append({"role": "user", "content": text})
                user_histories[chat_id] = user_histories[chat_id][-20:]
                reply = ask_claude(user_histories[chat_id])
                user_histories[chat_id].append({"role": "assistant", "content": reply})
                send_msg(chat_id, reply)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

threading.Thread(target=bot_loop, daemon=True).start()
HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
