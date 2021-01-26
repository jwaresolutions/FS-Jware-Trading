import config
import alpaca_trade_api as tradeapi

API_KEY = config.get_keys(request='key_id', dryrun=True)
SECRET_KEY = config.get_keys(request='secret_key', dryrun=True)
API_URL = config.get_keys(request='endpoint', dryrun=True)
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url=API_URL)

class submit_order:

def submit_order(self):
    api.submit_order(
        symbol=self.symbol,
        side='buy',
        type='market',
        qty='100',
        time_in_force='day',
        order_class='bracket',
        take_profit=dict(
            limit_price='305.0',
        ),
        stop_loss=dict(
            stop_price='295.5',
            limit_price='295.5',
        )
    )