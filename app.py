from flask import Flask, render_template, request, jsonify
import requests
import hmac
import hashlib
import time
import json

app = Flask(__name__)

# ==================== YOUR COINDCX API KEYS ====================
COINDCX_API_KEY = "97a302c3085279b828c3f8a39ad468185a75f4798de60bd8"
COINDCX_SECRET_KEY = "dc436326dd5c837feeaf2ab0eacdbaa6149cb4688167bb96effaa32184939536"

COINDCX_BASE_URL = "https://api.coindcx.com"

def place_coindcx_order(symbol, side, quantity):
    try:
        url = f"{COINDCX_BASE_URL}/exchange/v1/orders/create"
        secret_bytes = bytes(COINDCX_SECRET_KEY, encoding='utf-8')
        timeStamp = int(round(time.time() * 1000))
        
        body = {
            "timestamp": timeStamp,
            "order_type": "market_order",
            "side": side.lower(),
            "market": symbol,
            "total_quantity": float(quantity)
        }
        
        json_body = json.dumps(body, separators=(',', ':'))
        signature = hmac.new(secret_bytes, json_body.encode('utf-8'), hashlib.sha256).hexdigest()

        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-APIKEY': COINDCX_API_KEY,
            'X-AUTH-SIGNATURE': signature
        }

        res = requests.post(url, data=json_body, headers=headers, timeout=10)
        
        # Safely handle empty or non-JSON responses
        if res.text:
            try:
                return res.json()
            except Exception:
                return {"status_code": res.status_code, "response": res.text}
        else:
            return {"status_code": res.status_code, "message": "Server returned empty response"}
            
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/execute', methods=['POST'])
def execute():
    data = request.json
    raw_coin = data.get('coin', '').strip().upper()
    margin = data.get('margin', 6)

    clean_coin = raw_coin.replace("B-", "").replace("_USDT", "").replace("USDT", "").strip()
    coindcx_sym = f"{clean_coin}USDT"

    # Converting USDT margin to rough SOL quantity for Spot/Futures Order Execution
    # Assuming SOL ~ $75, 6 USDT gives approx 0.08 SOL
    sol_qty = round(float(margin) / 75.0, 2)
    if sol_qty <= 0:
        sol_qty = 0.08

    dcx_order = place_coindcx_order(coindcx_sym, "buy", sol_qty)

    return jsonify({
        "coindcx_response": dcx_order
    })

if __name__ == '__main__':
    app.run()
