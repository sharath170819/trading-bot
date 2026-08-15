from flask import Flask, render_template_string, request, jsonify
import requests
import hmac
import hashlib
import time
import json

app = Flask(__name__)

# ==================== YOUR API KEYS ====================
COINDCX_API_KEY = "c7435c4dedf99f9dca6e6dec64852d760d-d076e882388dad"
COINDCX_SECRET_KEY = "27345af623a67eed69-fa143b9e049a50e51b8ef2ef0dd5ce-f9fc61c135d7bff3"

MUDREX_API_KEY = "97f6c7b7-a80e-4423-880c-b217c75153bc"
MUDREX_SECRET_KEY = "Hrx8jVBcmgoGnhhwIPMwIC3f8I9TzAli"

# Corrected API Base Endpoints
COINDCX_BASE_URL = "https://api.coindcx.com"
MUDREX_BASE_URL = "https://trade.mudrex.com/fapi/v1"

def get_exchange_symbols(raw_coin):
    clean_coin = raw_coin.upper().replace("B-", "").replace("_USDT", "").replace("USDT", "").strip()
    coindcx_symbol = f"B-{clean_coin}_USDT"
    mudrex_symbol = f"{clean_coin}USDT"
    return clean_coin, coindcx_symbol, mudrex_symbol

def place_coindcx_order(symbol, side, leverage, margin):
    try:
        url = f"{COINDCX_BASE_URL}/exchange/v1/derivatives/futures/orders/create"
        secret_bytes = bytes(COINDCX_SECRET_KEY, encoding='utf-8')
        timeStamp = int(round(time.time() * 1000))
        
        body = {
            "timestamp": timeStamp,
            "order_type": "market_order",
            "side": side,
            "pair": symbol,
            "leverage": float(leverage),
            "margin": float(margin)
        }
        
        json_body = json.dumps(body)
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

def place_mudrex_order(symbol, side, leverage, margin):
    try:
        url = f"{MUDREX_BASE_URL}/order"
        
        body = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "MARKET",
            "leverage": float(leverage),
            "margin": float(margin)
        }

        # Updated Mudrex API Authentication Header
        headers = {
            'Content-Type': 'application/json',
            'X-Authentication': MUDREX_SECRET_KEY
        }

        res = requests.post(url, json=body, headers=headers, timeout=10)
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
                status.innerText = "COINDCX:\n" + JSON.stringify(data.coindcx_response, null, 2) + 
                                   "\n\nMUDREX:\n" + JSON.stringify(data.mudrex_response, null, 2);
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

    clean_coin, coindcx_sym, mudrex_sym = get_exchange_symbols(raw_coin)

    dcx_order = place_coindcx_order(coindcx_sym, "buy", leverage, margin)
    mud_order = place_mudrex_order(mudrex_sym, "SELL", leverage, margin)

    return jsonify({
        "coindcx_response": dcx_order,
        "mudrex_response": mud_order
    })

if __name__ == '__main__':
    app.run()
