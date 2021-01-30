import sqlite3, alpaca_connection
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
dst_check = get_date_isoformat('2020-11-07')[-6:]

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
end_minute_bar = f"{current_date} 16:00:00{dst_check}"

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
    after_opening_range_breakdown = after_opening_range_bars[after_opening_range_bars['close'] < opening_range_low]

    current_price = after_opening_range_bars.iloc[0]['close']
    sma_20_breakout = False
    sma_20_breakdown = False
    sma_50_breakout = False
    sma_50_breakdown = False
    overbought = False
    oversold = False

    if current_price.item() > sma_20[0]:
        sma_20_breakout = True
    if current_price.item() < sma_20[0]:
        sma_20_breakdown = True
    if current_price.item() > sma_50[0]:
        sma_50_breakout = True
    if current_price.item() < sma_50[0]:
        sma_50_breakdown = True
    if rsi_14[0] > 70:
        overbought = True
    if rsi_14[0] < 30:
        oversold = True

    # Breakout Logic
    if not after_opening_range_breakout.empty and symbol not in existing_order_symbols and sma_20_breakout and sma_50_breakout:
        neworder = True
        limit_price = after_opening_range_breakout.iloc[0]['close']
        messages.append(
            f"placing order for {symbol} at {limit_price}, closed above {opening_range_high}\n\n{after_opening_range_breakout.iloc[0]['close']}\n\n")
        print(
            f"placing order for {symbol} at {limit_price}, closed above {opening_range_high}\n\n{after_opening_range_breakout.iloc[0]['close']}\n\n")
        order(symbol, 'buy', limit_price, limit_price + opening_range, limit_price - opening_range)
    # Breakdown Logic
    elif not after_opening_range_breakdown.empty and symbol not in existing_order_symbols and sma_20_breakdown and sma_50_breakdown:
        messages.append(
            f"placing order for {symbol} at {limit_price}, closed below {opening_range_low}\n\n{after_opening_range_breakdown.iloc[0]['close']}\n\n")
        print(
            f"placing order for {symbol} at {limit_price}, closed below {opening_range_low}\n\n{after_opening_range_breakdown.iloc[0]['close']}\n\n")
        order(symbol, 'sell', limit_price, limit_price - opening_range, limit_price + opening_range)
    elif symbol in existing_order_symbols:
        print(f"Order for {symbol} already exists, current list of orders {existing_order_symbols}")
    else:
        print(f"{symbol} did not match this strategy at {get_date_isoformat(current_date)}")

if not messages:
    send_message(messages)
