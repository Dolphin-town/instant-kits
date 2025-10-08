import os, time, requests, json
from flask import Flask          # keeps Render happy (port binding)
app = Flask(__name__)            # required by Render even if unused

BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT  = os.getenv("TG_ADMIN_CHAT")
GPT4ALL_MODEL = "orca-mini-3b-gguf2-q4_0.gguf"   # light & fast
import gpt4all
model = gpt4all.GPT4All(GPT4ALL_MODEL)

def reply(text):
    prompt = open("agent_prompt.txt").read() + "\n\nQ: " + text + "\nA:"
    return model.generate(prompt, max_tokens=90, temp=0.3)

def send_msg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": ADMIN_CHAT, "text": text}
    requests.post(url, json=payload, timeout=10)

@app.route("/")                 # Render health-check
def health():
    return "AI agent alive", 200

if __name__ == "__main__":
    # start Flask (keeps service green) + poll loop
    from threading import Thread
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))).start()

    offset = 0
    while True:
        updates = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}").json().get("result", [])
        for u in updates:
            offset = u["update_id"] + 1
            if "message" not in u: continue
            m = u["message"]
            if str(m["chat"]["id"]) != str(ADMIN_CHAT): continue   # ignore others
            ans = reply(m["text"])
            send_msg(ans)
        time.sleep(2)
