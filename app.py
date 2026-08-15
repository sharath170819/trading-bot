from flask import Flask, render_template_string, request, jsonify
import requests
import hmac
import hashlib
import time
import json

app = Flask(__name__)

# ==================== UPDATED API KEYS ====================
COINDCX_API_KEY = "97a302c3085279b828c3f8a39ad468185a75f4798de60bd8"
COINDCX_SECRET_KEY = "dc436326dd5c837feeaf2ab0eacdbaa6149cb4688167bb96effaa32184939536"

MUDREX_API_KEY = "97f6c7b7-a80e-4423-880c-b217c75153bc"
MUDREX_SECRET_KEY = "Hrx8jVBcmgoGnhhwIPMwIC3f8I9TzAli"

COINDCX_BASE_URL = "https://api.coindcx.com"

def place_coindcx_order(symbol, side, leverage, margin):
    try:
        url = f"{COINDCX_BASE_URL}/exchange/v1/derivatives/futures/orders/create"
        secret_bytes = bytes(COINDCX_SECRET_KEY, encoding='utf-8')
        timeStamp = int(round(time.time() * 1000))
        
        body = {
            "timestamp": timeStamp,
            "order_type": "market_order",
            "side": side.lower(),
            "pair": symbol,
            "leverage": float(leverage),
            "margin": float(margin)
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

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dual Hedge Executor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #fff; text-align: center; padding: 20px; }
        .card { background: #1e1e1e; max-width: 450px; margin: 0 auto; padding: 20px; border-radius: 10px; border: 1px solid #333; }
        h2 { color: #00e676; }
        input { width: 100%; padding: 10px; margin: 8px 0; border-radius: 5px; border: 1px solid #444; background: #222; color: #fff; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #00e676; border: none; font-weight: bold; font-size: 16px; border-radius: 5px; cursor: pointer; margin-top: 10px; }
        #status { margin-top: 15px; font-weight: bold; font-size: 12px; text-align: left; background: #111; padding: 10px; border-radius: 5px; white-space: pre-wrap; color: #ffeb3b; word-break: break-all; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Live Cross-Hedge Executor</h2>
        <input type="text" id="coin" placeholder="Coin Name" value="SOL">
        <input type="number" id="leverage" placeholder="Leverage" value="10">
        <input type="number" id="margin" placeholder="Margin USDT" value="1">
        <button type="button" onclick="runHedge()">EXECUTE LIVE HEDGE</button>
        <div id="status">Ready...</div>
    </div>

    <script>
        function runHedge() {
            var status = document.getElementById('status');
            status.style.color = '#ffeb3b';
            status.innerText = 'Connecting to Exchanges... Please wait.';

            var coinVal = document.getElementById('coin').value;
            var levVal = document.getElementById('leverage').value;
            var marginVal = document.getElementById('margin').value;

            fetch('/execute', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    coin: coinVal,
                    leverage: levVal,
                    margin: marginVal
                })
            })
            .then(function(res) { return res.json(); })
            .then(function(data) {
                status.style.color = '#00e676';
                status.innerText = "COINDCX:\\n" + JSON.stringify(data.coindcx_response, null, 2);
            })
            .catch(function(err) {
                status.style.color = '#ff5252';
                status.innerText = 'Server Error: ' + err;
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

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
