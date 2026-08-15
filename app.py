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
        
        # Payload for CoinDCX Futures Market Order
        body = {
            "timestamp": timeStamp,
            "order_type": "market_order",
            "side": side.lower(),       # 'buy' or 'sell'
            "pair": symbol,             # e.g., 'B-SOL_USDT'
            "leverage": int(leverage),  # Leverage level
            "total_quantity": float(quantity) # Quantity of coin (e.g. 1 or 0.1)
        }
        
        json_body = json.dumps(body, separators=(',', ':'))
        signature = hmac.new(secret_bytes, json_body.encode('utf-8'), hashlib.sha256).hexdigest()

        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-APIKEY': COINDCX_API_KEY,
            'X-AUTH-SIGNATURE': signature
        }

        res = requests.post(url, data=json_body, headers=headers, timeout=10)
        
        # Detailed Response Parsing for Debugging
        try:
            return res.json()
        except Exception:
            return {
                "status_code": res.status_code, 
                "raw_response": res.text if res.text else "Empty response body from CoinDCX",
                "headers": dict(res.headers)
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
    margin = data.get('margin') # treating input as quantity/size

    clean_coin = raw_coin.upper().replace("B-", "").replace("_USDT", "").replace("USDT", "").strip()
    coindcx_sym = f"B-{clean_coin}_USDT"

    dcx_order = place_coindcx_order(coindcx_sym, "buy", leverage, margin)

    return jsonify({
        "coindcx_response": dcx_order
    })

if __name__ == '__main__':
    app.run()
