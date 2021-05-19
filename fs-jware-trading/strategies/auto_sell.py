import ssl, smtplib
from time import sleep

import API.alpaca_connection as alpaca_connection
from datetime import date
import alpaca_trade_api as tradeapi


alpaca_connect = alpaca_connection.Alpaca_Connect()
API_KEY = alpaca_connect.key_id
SECRET_KEY = alpaca_connect.secret_key
API_URL = alpaca_connect.endpoint
current_date = date.today().isoformat()
context = ssl.create_default_context()
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url=API_URL)
positions = api.list_positions()

def get_recent_bars():
    for i in range(len(positions)):
