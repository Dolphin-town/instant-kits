import os, time, jwt, requests
from flask import Flask, request, send_file, render_template

# ---------- CONFIG ----------
NOW_KEY         = os.getenv("NOWPAYMENTS_API_KEY")
WEBHOOK_SECRET  = os.getenv("NOWPAYMENTS_IPN_SECRET")
KIT_PRICE       = 250
USDT_ADDRESS    = os.getenv("USDT_TRC20")          
BOT_TOKEN       = os.getenv("TELEGRAM_BOT_TOKEN")  
TG_ADMIN_CHAT   = os.getenv("TG_ADMIN_CHAT")       
# ----------------------------

app = Flask(__name__)

# ---------- HELPERS ----------
def create_invoice(usd_value):
    headers = {"x-api-key": NOW_KEY, "Content-Type": "application/json"}
    body = {
        "price_amount": usd_value,
        "price_currency": "usd",
        "pay_currency": "usdttrc20",
        "order_id": str(int(time.time() * 1000)),
        "order_description": "Launch Conversion Kit #1",
        "ipn_callback_url": "https://launchakit.onrender.com/webhook",
        "success_url": "https://launchakit.onrender.com/success"
    }
    r = requests.post("https://api.nowpayments.io/v1/invoice", json=body, headers=headers)
    return r.json().get("invoice_url"), r.json().get("id")

def send_telegram(dl_link):
    msg = f"🎉 Payment confirmed!\nDownload your kit: {dl_link}\nLink expires in 60 min."
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_ADMIN_CHAT, "text": msg}
    requests.post(url, json=payload, timeout=5)
# ------------------------------

@app.route("/create-order", methods=["POST"])
def order():
    url, inv_id = create_invoice(KIT_PRICE)
    return {"invoice_url": url, "invoice_id": inv_id}

@app.route("/webhook", methods=["POST"])
def hook():
    if request.headers.get("x-nowpayments-sig") != WEBHOOK_SECRET:
        return "fail", 400
    data = request.get_json()
    if data.get("payment_status") == "finished":
        token = jwt.encode({"id": data["invoice_id"], "exp": int(time.time()) + 3600},
                           WEBHOOK_SECRET, algorithm="HS256")
        send_telegram(f"https://launchakit.onrender.com/dl/{token}")
    return "ok", 200

@app.route("/dl/<token>")
def download(token):
    try:
        jwt.decode(token, WEBHOOK_SECRET, algorithms=["HS256"])
    except Exception:
        return "Expired or invalid", 404
    return send_file("kits/launch-kit-01.zip", as_attachment=True)

@app.route("/success")
def success():
    return "<h3>Payment confirmed – your download link was sent.</h3>"

@app.route("/")
def home():
    return render_template("index.html")
