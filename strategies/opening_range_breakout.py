import sqlite3
import config
import alpaca_trade_api as tradeapi
from datetime import date


API_KEY = config.get_keys(request='key_id', dryrun=False)
SECRET_KEY = config.get_keys(request='secret_key', dryrun=False)
API_URL = config.get_keys(request='endpoint', dryrun=False)

connection = sqlite3.connect(config.db_path)
connection.row_factory = sqlite3.Row

cursor = connection.cursor()

cursor.execute("""
    select id from strategy where name = 'opening_range_breakout'
""")

strategy_id = cursor.fetchone()['id']

cursor.execute("""
    select symbol, name
    from stock
    join stock_strategy on stock_strategy.stock_id = stock.id
    where stock_strategy.strategy_id = ?
""", (strategy_id,))

stocks = cursor.fetchall()
symbols = [stock['symbol'] for stock in stocks]
print(symbols)

api = tradeapi.REST(API_KEY, SECRET_KEY, base_url=API_URL)
current_date = date.today().isoformat()
start_minute_bar = f"{current_date} 09:30:00-05:00"
end_minute_bar = f"{current_date} 09:45:00-05:00"

for symbol in symbols:
    minute_bars = api.polygon.historic_agg_v2(symbol, 1, 'minute', _from=current_date, to=current_date).df
    print(symbol)
    opening_range_mask = (minute_bars.index >= start_minute_bar) & (minute_bars.index < end_minute_bar)
    opening_range_bars = minute_bars.loc[opening_range_mask]
    opening_range_low = opening_range_bars['low'].min()
    opening_range_high = opening_range_bars['low'].max()
    opening_range = opening_range_high - opening_range_low
    after_opening_range_mask = minute_bars.index <= end_minute_bar
    after_opening_range_bars = minute_bars.loc[after_opening_range_mask]
    after_opening_range_breakout = after_opening_range_bars[after_opening_range_bars['close'] > opening_range_high]

    if not after_opening_range_breakout.empty:
        limit_price = after_opening_range_breakout.iloc[0]['close']
        print(f"placing order for {symbol} at {limit_price}, closed above {opening_range_high} at {after_opening_range_breakout.iloc[0]['close']}")



