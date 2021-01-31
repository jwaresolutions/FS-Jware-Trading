import alpaca_connection
import sqlite3, pandas
from datetime import datetime, timedelta, date
from strategies.Helpers import api_call

alpaca_connect = alpaca_connection.Alpaca_Connect()
connection = sqlite3.connect(alpaca_connect.db_path)
connection.row_factory = sqlite3.Row
api = api_call()
cursor = connection.cursor()

cursor.execute("""
    select symbol, stock_strategy.stock_id
    from stock
    join stock_strategy on stock_strategy.stock_id = stock.id
    join stock_price on stock.id = stock_price.stock_id
    where date = ? and strategy_id = 1
""", ('2021-01-29',))

stocks = cursor.fetchall()

symbols = [stock['symbol'] for stock in stocks]
stock_id = [stock['stock_id'] for stock in stocks]
stocks_dict = dict(zip(symbols, stock_id))

for symbol in stocks_dict:
    today = date.today()
    end_date_range = today - timedelta(days=today.weekday())
    start_date = end_date_range - timedelta(weeks=52)

    while start_date < end_date_range:
        end_date = start_date + timedelta(days=4)
        print(symbol)
        minutes = api.polygon.historic_agg_v2(symbol, 1, 'minute', _from=start_date, to=end_date).df
        minutes = minutes.resample('1min').ffill()
        print(minutes)
        for index, row in minutes.iterrows():
            cursor.execute("""
                INSERT INTO stock_price_minute (stock_id, datetime, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (stocks_dict[symbol], index.tz_localize(None).isoformat(), row['open'], row['high'], row['low'], row['close'],
                  row['volume']))

        connection.commit()
        start_date = start_date + timedelta(days=7)
