import sqlite3
import config
import alpaca_trade_api as tradeapi
from datetime import date
import smtplib, ssl
from timezone import is_dst

context = ssl.create_default_context()
messages = []
current_date = date.today().isoformat()
API_KEY = config.get_keys(request='key_id', dryrun=True)
SECRET_KEY = config.get_keys(request='secret_key', dryrun=True)
API_URL = config.get_keys(request='endpoint', dryrun=True)
neworder = False
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url=API_URL)

orders = api.list_orders(status='all', after=f"{current_date}T13:30:00Z")
existing_order_symbols = [order.symbol for order in orders if order != 'cancled']
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
        print(f"Order for {symbol} alredy exists, current list of orders {existing_order_symbols}")


print(messages)
if neworder == True:
    neworder = False
    with smtplib.SMTP_SSL(config.email_host, config.email_port, context=context) as server:
        server.login(config.email_address, config.email_password)
        email_message = f"Subject: Trade Notification for {current_date}\n\n"
        email_message += "\n\n".join(messages)
        server.sendmail(config.email_address, config.email_address, email_message)
        server.sendmail(config.email_address, config.email_sms, email_message)

