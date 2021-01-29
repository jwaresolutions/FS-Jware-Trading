import smtplib
import sqlite3, ssl
import alpaca_trade_api as tradeapi
from datetime import date
from DaylightSaveingsTimeCheck import is_dst
import alpaca_connection

context = ssl.create_default_context()
messages = []
current_date = date.today().isoformat()
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

if is_dst():
    start_minute_bar = f"{current_date} 09:30:00-04:00"
    end_minute_bar = f"{current_date} 09:45:00-04:00"
else:
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

    if not after_opening_range_breakout.empty and symbol not in existing_order_symbols:
        neworder = True
        limit_price = after_opening_range_breakout.iloc[0]['close']
        messages.append(f"placing order for {symbol} at {limit_price}, closed above {opening_range_high}\n\n{after_opening_range_breakout.iloc[0]['close']}\n\n")
        print(
            f"placing order for {symbol} at {limit_price}, closed above {opening_range_high}\n\n{after_opening_range_breakout.iloc[0]['close']}\n\n")

        api.submit_order(
            symbol=symbol,
            side='buy',
            type='limit',
            qty='1',
            time_in_force='day',
            order_class='bracket',
            limit_price=limit_price,
            take_profit=dict(
                limit_price=limit_price + opening_range,
            ),
            stop_loss=dict(
                stop_price=limit_price - opening_range,
            )
        )

    else:
        print(f"Order for {symbol} already exists, current list of orders {existing_order_symbols}")


print(messages)
if neworder == True:
    neworder = False
    with smtplib.SMTP_SSL(alpaca_connect.email_host, alpaca_connect.email_port, context=context) as server:
        server.login(alpaca_connect.email_address, alpaca_connect.email_password)
        email_message = f"Subject: Trade Notification for {current_date}\n\n"
        email_message += "\n\n".join(messages)
        server.sendmail(alpaca_connect.email_address, alpaca_connect.email_address, email_message)
        server.sendmail(alpaca_connect.email_address, alpaca_connect.email_sms, email_message)
