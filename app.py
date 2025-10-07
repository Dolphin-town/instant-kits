import os, json, jwt, time, requests
from flask import Flask, request, redirect, send_file
NOW_KEY   = os.getenv("NOWPAYMENTS_API_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN")
KIT_PRICE = 250
USDT_ADDRESS = os.getenv("USDT_TRC20")  # your wallet

app = Flask(__name__)
def create_invoice(usd_value):
    headers = {"x-api-key": NOW_KEY, "Content-Type": "application/json"}
    body = {"price_amount": usd_value,
            "price_currency": "usd",
            "pay_currency": "usdttrc20",
            "order_id": str(int(time.time()*1000)),
            "order_description": "Launch Conversion Kit #1",
            "ipn_callback_url": "https://your-render/webhook",
            "success_url": "https://your-render/success?token=__TOKEN__"}
    r = requests.post("https://api.nowpayments.io/v1/invoice", json=body, headers=headers)
    return r.json().get("invoice_url"), r.json().get("id")

@app.route("/create-order", methods=["POST"])
def order():
    url, inv_id = create_invoice(KIT_PRICE)
    return {"invoice_url": url, "invoice_id": inv_id}

@app.route("/webhook", methods=["POST"])
def hook():
    sig = request.headers.get("x-nowpayments-sig")
    if not sig or sig != WEBHOOK_SECRET: return "fail", 400
    data = request.get_json()
    if data.get("payment_status") == "finished":
        token = jwt.encode({"id": data["invoice_id"], "exp": int(time.time())+3600},
                           WEBHOOK_SECRET, algorithm="HS256")
        # Telegram DM optional here
        send_telegram(data["order_id"], token)
    return "ok", 200

def send_telegram(order_id, token):
    chat_id = os.getenv("TG_ADMIN_CHAT")  # your Telegram user ID
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    dl = f"https://your-render/dl/{token}"
    txt = f"New sale {order_id}\nDownload: {dl}"
    requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage",
                  json={"chat_id": chat_id, "text": txt})

@app.route("/dl/<token>")
def download(token):
    try:
        jwt.decode(token, WEBHOOK_SECRET, algorithms=["HS256"])
    except: return "Expired or invalid", 404
    return send_file("kits/launch-kit-01.zip", as_attachment=True)

@app.route("/success")
def success():
    return "<h3>Payment confirmed – your download link was sent via Telegram / email.</h3>"
