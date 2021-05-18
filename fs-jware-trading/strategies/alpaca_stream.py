from alpaca_trade_api import Stream
from alpaca_trade_api.common import URL
import API.alpaca_connection as alpaca_connection
import alpaca_trade_api as tradeapi

alpaca_connect = alpaca_connection.Alpaca_Connect()
API_KEY = alpaca_connect.key_id
SECRET_KEY = alpaca_connect.secret_key
API_URL = alpaca_connect.endpoint
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url=API_URL)


async def trade_callback(t):
    print(t)

stream = Stream(API_KEY,
                     SECRET_KEY,
                     base_url=URL(API_URL),
                     data_feed='sip')  # <- replace to SIP if you have PRO subscription

def subscribe(symbol, method):
    if method == 'trades':
        stream.subscribe_trade_updates(trade_callback)



subscribe('AAPL', 'trades')
stream.run()


