from API import alpaca_connection
import sqlite3, numpy, tulipy
from datetime import timedelta, date
from strategies.Helpers import api_call
import time

alpaca_connect = alpaca_connection.Alpaca_Connect()
connection = sqlite3.connect(alpaca_connect.db_path)
connection.row_factory = sqlite3.Row
api = api_call()
cursor = connection.cursor()

sleep_count = 0
today = date.today()
end_date_range = today - timedelta(days=today.weekday())

cursor.execute("""
    select DISTINCT symbol, stock_strategy.stock_id
    from stock
    join stock_strategy on stock_strategy.stock_id = stock.id
    join stock_price on stock.id = stock_price.stock_id
    WHERE strategy_id = 1
""")

stocks = cursor.fetchall()

symbols = [stock['symbol'] for stock in stocks]
stock_id = [stock['stock_id'] for stock in stocks]
stocks_dict = dict(zip(symbols, stock_id))

for symbol in stocks_dict:
    recent_closes = []
    start_date = end_date_range - timedelta(weeks=52)

    while start_date < end_date_range:
        if sleep_count >= 199:
            time.sleep(70)
            sleep_count = 0
        end_date = start_date + timedelta(days=4)
        minutes = api.polygon.historic_agg_v2(symbol, 1, 'minute', _from=start_date, to=end_date).df
        sleep_count = sleep_count + 1
        minutes = minutes.resample('1min').ffill()
        for index, row in minutes.iterrows():
            recent_closes.append(row['close'])
            if len(recent_closes) >= 50:
                sma_20 = tulipy.sma(numpy.array(recent_closes), period=20)[-1]
                sma_50 = tulipy.sma(numpy.array(recent_closes), period=50)[-1]
                rsi_14 = tulipy.rsi(numpy.array(recent_closes), period=14)[-1]
            else:
                sma_20, sma_50, rsi_14 = None, None, None
            # cursor.execute("""
            #     INSERT INTO stock_price_minute (stock_id, datetime, open, high, low, close, volume, sma_20, sma_50, rsi_14)
            #     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            # """, (stocks_dict[symbol], index.tz_localize(None).isoformat(), row['open'], row['high'], row['low'],
            #       row['close'], row['volume'], sma_20, sma_50, rsi_14))
        print(f"== COUNTER = {sleep_count} == Fetching minute bars for {symbol} {start_date} - {end_date} ==")
        start_date = start_date + timedelta(days=7)
# connection.commit()
