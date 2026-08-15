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

def place_coindcx_futures_order(symbol, side, leverage, target_usdt):
    try:
        # Dedicated CoinDCX Futures Endpoint
        url = f"{COINDCX_BASE_URL}/exchange/v1/derivatives/futures/orders/create"
        secret_bytes = bytes(COINDCX_SECRET_KEY, encoding='utf-8')
        timeStamp = int(round(time.time() * 1000))
        
        # Calculate SOL quantity using leverage margin (Margin USDT * Leverage / SOL Price)
        # 6 USDT margin at 10x leverage = $60 position size (~0.79 SOL)
        sol_price = 75.5  # Approx SOL Price
        calc_quantity = round((float(target_usdt) * int(leverage)) / sol_price, 2)
        if calc_quantity <= 0:
            calc_quantity = 0.1

        body = {
            "timestamp": timeStamp,
            "order_type": "market_order",
            "side": side.lower(),       # 'buy' or 'sell'
            "pair": symbol,             # e.g., 'B-SOL_USDT'
            "leverage": int(leverage),   # 10
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
    leverage = data.get('leverage', 10)
    margin = data.get('margin', 6) 

    clean_coin = raw_coin.replace("B-", "").replace("_USDT", "").replace("USDT", "").strip()
    coindcx_sym = f"B-{clean_coin}_USDT"

    dcx_order = place_coindcx_futures_order(coindcx_sym, "buy", leverage, margin)

    return jsonify({
        "coindcx_response": dcx_order
    })

if __name__ == '__main__':
    app.run()
