from flask import Flask, render_template, request, jsonify
import requests
import hmac
import hashlib
import time
import json

app = Flask(__name__)

# ==================== COINDCX API KEYS ====================
COINDCX_API_KEY = "97a302c3085279b828c3f8a39ad468185a75f4798de60bd8"
COINDCX_SECRET_KEY = "dc436326dd5c837feeaf2ab0eacdbaa6149cb4688167bb96effaa32184939536"

COINDCX_BASE_URL = "https://api.coindcx.com"

def place_coindcx_futures_order(pair, side, leverage, margin_usdt):
    try:
        url = f"{COINDCX_BASE_URL}/exchange/v1/derivatives/futures/orders/create"
        secret_bytes = bytes(COINDCX_SECRET_KEY, encoding='utf-8')
        timeStamp = int(round(time.time() * 1000))

        # SOL Price ~ $75.5
        # Quantity calculation formatted properly for Futures contract decimal precision
        calc_qty = (float(margin_usdt) * int(leverage)) / 75.5
        total_qty = round(calc_qty, 1)  # Futures requires 1 decimal precision for SOL
        if total_qty <= 0:
            total_qty = 0.1

        body = {
            "timestamp": timeStamp,
            "order_type": "market_order",
            "side": side.lower(),       # "buy"
            "pair": pair,               # "B-SOL_USDT"
            "leverage": int(leverage),   # 10
            "total_quantity": total_qty
        }

        json_body = json.dumps(body, separators=(',', ':'))
        signature = hmac.new(secret_bytes, json_body.encode('utf-8'), hashlib.sha256).hexdigest()

        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-APIKEY': COINDCX_API_KEY,
            'X-AUTH-SIGNATURE': signature
        }

        res = requests.post(url, data=json_body, headers=headers, timeout=10)

        # Handle API response accurately
        if res.status_code == 200:
            return res.json()
        else:
            try:
                return {"status_code": res.status_code, "error_details": res.json()}
            except Exception:
                return {"status_code": res.status_code, "raw_response": res.text}

    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/execute', methods=['POST'])
def execute():
    data = request.json
    raw_coin = data.get('coin', '').strip().upper()
    leverage = data.get('leverage', 10)
    margin = data.get('margin', 6)

    clean_coin = raw_coin.replace("B-", "").replace("_USDT", "").replace("USDT", "").strip()
    coindcx_futures_pair = f"B-{clean_coin}_USDT"

    dcx_order = place_coindcx_futures_order(coindcx_futures_pair, "buy", leverage, margin)

    return jsonify({
        "coindcx_response": dcx_order
    })

if __name__ == '__main__':
    app.run()
