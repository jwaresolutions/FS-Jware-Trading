import sqlite3, alpaca_connection, tulipy
import alpaca_trade_api as tradeapi
from datetime import date, datetime
from pytz import timezone
from Orders import order, send_message


def get_date_isoformat(_date=None):
    tz = timezone('America/New_York')
    _date = datetime.strptime(f'{_date}', '%Y-%m-%d').astimezone(tz)
    _date = _date.isoformat()
    return _date


print(datetime.now())
current_date = date.today().isoformat()
strategy_name = 'opening_range_break_out_down'
dst_check = get_date_isoformat(current_date)[-6:]

messages = []
alpaca_connect = alpaca_connection.Alpaca_Connect()
API_KEY = alpaca_connect.key_id
SECRET_KEY = alpaca_connect.secret_key
API_URL = alpaca_connect.endpoint
db_path = alpaca_connect.db_path
neworder = False
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url=API_URL)

orders = api.list_orders(status='all', after=f"{current_date}T13:30:00Z")
existing_order_symbols = [order.symbol for order in orders if order != 'canceled']
print(f"EXISTING SYMBOLS {existing_order_symbols}")
connection = sqlite3.connect(db_path)
connection.row_factory = sqlite3.Row

cursor = connection.cursor()

cursor.execute("""
    select id from strategy where name = ?
""", (strategy_name,))

strategy_id = cursor.fetchone()['id']

cursor.execute("""
    select symbol, name,date,rsi_14, sma_20, sma_50, close
    from stock
    join stock_strategy on stock_strategy.stock_id = stock.id
    join stock_price on stock.id = stock_price.stock_id
    where date = ? and strategy_id = ?
""", (current_date, strategy_id))

stocks = cursor.fetchall()

symbols = [stock['symbol'] for stock in stocks]
rsi_14 = [stock['rsi_14'] for stock in stocks]
sma_20 = [stock['sma_20'] for stock in stocks]
sma_50 = [stock['sma_50'] for stock in stocks]
close = [stock['close'] for stock in stocks]

indicator_values = {}
for symbol in symbols:
    i = 0
    indicator_values[symbol] = {
        "rsi_14": rsi_14[i],
        "sma_20": sma_20[i],
        "sma_50": sma_50[i],
        "close": close[i]
    }
    i += 1

start_minute_bar = f"{current_date} 09:30:00{dst_check}"
end_minute_bar = f"{current_date} 12:19:00{dst_check}"

for symbol in symbols:
    minute_bars = api.polygon.historic_agg_v2(symbol, 1, 'minute', _from=current_date, to=current_date).df
    minute_bars = minute_bars.resample('1min').ffill()
    market_open_mask = (minute_bars.index >= start_minute_bar) & (minute_bars.index < end_minute_bar)
    market_open_bars = minute_bars.loc[market_open_mask]
    if len(market_open_bars) >= 20:
        closes = market_open_bars.close.values
        lower, middle, upper = tulipy.bbands(closes, 20, 2.5)
        print(lower[-1])
        current_candle = market_open_bars.iloc[-1]
        previous_candle = market_open_bars.iloc[-2]
        limit_price = current_candle.close
        current_candle_range = current_candle.high - current_candle.low
        if current_candle.close > lower[-1] and previous_candle.close < lower[
            -2] and symbol not in existing_order_symbols:
            print(current_candle)
            profit_price = limit_price + (current_candle_range * 3)
            stop_price = previous_candle.low
            order(symbol, 'buy', limit_price, profit_price, stop_price)
            messages.append(f"{symbol} closed above lower bollinger band purchasing at {limit_price}")
        elif current_candle.close < upper[-1] and previous_candle.close > upper[
            -2] and symbol not in existing_order_symbols:
            print(current_candle)
            profit_price = limit_price - (current_candle_range * 3)
            stop_price = previous_candle.high
            order(symbol, 'sell', limit_price, profit_price, stop_price)
            messages.append(f"{symbol} closed above lower bollinger band purchasing at {limit_price}")
        elif symbol in existing_order_symbols:
            print(f"Order for {symbol} already exists, current list of orders {existing_order_symbols}")
        else:
            print(f"{symbol} did not match this strategy at {get_date_isoformat(current_date)}")

if not messages:
    send_message(messages)
