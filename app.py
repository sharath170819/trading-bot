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

def get_sol_price():
    try:
        url = f"{COINDCX_BASE_URL}/exchange/ticker"
        res = requests.get(url, timeout=5).json()
        for item in res:
            if item.get('market') == 'SOLUSDT':
                return float(item.get('last_price', 0))
    except Exception:
        pass
    return 200.0  # Fallback price if API ticker fails

def place_coindcx_order(market_symbol, side, target_usdt):
    try:
        url = f"{COINDCX_BASE_URL}/exchange/v1/orders/create"
        secret_bytes = bytes(COINDCX_SECRET_KEY, encoding='utf-8')
        timeStamp = int(round(time.time() * 1000))
        
        # Calculate quantity based on USDT amount input
        sol_price = get_sol_price()
        calc_quantity = round(float(target_usdt) / sol_price, 3)
        if calc_quantity <= 0:
            calc_quantity = 0.01

        body = {
            "timestamp": timeStamp,
            "order_type": "market_order",
            "side": side.lower(),
            "market": market_symbol,
            "total_quantity": calc_quantity
        }
        
        json_body = json.dumps(body, separators=(',', ':'))
        signature = hmac.new(secret_bytes, json_body.encode('utf-8'), hashlib.sha256).hexdigest()

        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-APIKEY': COINDCX_API_KEY,
            'X-AUTH-SIGNATURE': signature
        }

        res = requests.post(url, data=json_body, headers=headers, timeout=10)
        return res.json()
            
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/execute', methods=['POST'])
def execute():
    data = request.json
    raw_coin = data.get('coin', '').strip().upper()
    margin = data.get('margin') 

    clean_coin = raw_coin.replace("B-", "").replace("_USDT", "").replace("USDT", "").strip()
    coindcx_sym = f"{clean_coin}USDT"

    dcx_order = place_coindcx_order(coindcx_sym, "buy", margin)

    return jsonify({
        "coindcx_response": dcx_order
    })

if __name__ == '__main__':
    app.run()
