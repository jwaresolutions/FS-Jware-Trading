from API import alpaca_connection
import alpaca_trade_api as tradeapi
from Orders import send_message

alpaca_connect = alpaca_connection.Alpaca_Connect()
API_KEY = alpaca_connect.key_id
SECRET_KEY = alpaca_connect.secret_key
API_URL = alpaca_connect.endpoint

api = tradeapi.REST(API_KEY, SECRET_KEY, base_url=API_URL)

response = api.close_all_positions()

if not response:
    send_message(response)
