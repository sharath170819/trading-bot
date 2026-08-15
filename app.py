from flask import Flask, render_template, request, jsonify
import requests
import hmac
import hashlib
import time
import json

app = Flask(__name__)

# ==================== YOUR API KEYS ====================
COINDCX_API_KEY = "97a302c3085279b828c3f8a39ad468185a75f4798de60bd8"
COINDCX_SECRET_KEY = "dc436326dd5c837feeaf2ab0eacdbaa6149cb4688167bb96effaa32184939536"

COINDCX_BASE_URL = "https://api.coindcx.com"

def place_coindcx_order(symbol, side, leverage, quantity):
    try:
        url = f"{COINDCX_BASE_URL}/exchange/v1/derivatives/futures/orders/create"
        secret_bytes = bytes(COINDCX_SECRET_KEY, encoding='utf-8')
        timeStamp = int(round(time.time() * 1000))
        
        body = {
            "timestamp": timeStamp,
            "order_type": "market_order",
            "side": side.lower(),
            "pair": symbol,
            "leverage": int(leverage),
            "total_quantity": float(quantity)
        }
        
        json_body = json.dumps(body, separators=(',', ':'))
        signature = hmac.new(secret_bytes, json_body.encode('utf-8'), hashlib.sha256).hexdigest()

        # Both key variations added to ensure authentication token is recognized
        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-APIKEY': COINDCX_API_KEY,
            'X-AUTH-KEY': COINDCX_API_KEY,
            'X-AUTH-SIGNATURE': signature
        }

        res = requests.post(url, data=json_body, headers=headers, timeout=10)
        
        try:
            return res.json()
        except Exception:
            return {
                "status_code": res.status_code,
                "raw_response": res.text
            }
            
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/execute', methods=['POST'])
def execute():
    data = request.json
    raw_coin = data.get('coin')
    leverage = data.get('leverage')
    margin = data.get('margin')

    clean_coin = raw_coin.upper().replace("B-", "").replace("_USDT", "").replace("USDT", "").strip()
    coindcx_sym = f"B-{clean_coin}_USDT"

    dcx_order = place_coindcx_order(coindcx_sym, "buy", leverage, margin)

    return jsonify({
        "coindcx_response": dcx_order
    })

if __name__ == '__main__':
    app.run()
