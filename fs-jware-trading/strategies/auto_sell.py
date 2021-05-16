import ssl, smtplib
import API.alpaca_connection as alpaca_connection
from datetime import date
import alpaca_trade_api as tradeapi







class sell:
    def __init__(self):
        self.alpaca_connect = alpaca_connection.Alpaca_Connect()
        self.API_KEY = self.alpaca_connect.key_id
        self.SECRET_KEY = self.alpaca_connect.secret_key
        self.API_URL = self.alpaca_connect.endpoint
        self.current_date = date.today().isoformat()
        self.context = ssl.create_default_context()
        self.api = tradeapi.REST(self.API_KEY, self.SECRET_KEY, base_url=self.API_URL)
        self.symbol = ''

    def get_recent_bars(self):
        pass
    '''
    get historical data for a symbol
    continue to get historical data for a symbol
    streem live data for a symbol
    
    calculate current rsi/sma-long/sma-short
    
    make decision to sell or not sell
    
    
    '''