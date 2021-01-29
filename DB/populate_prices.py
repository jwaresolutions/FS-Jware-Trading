import sqlite3, numpy, tulipy
import alpaca_trade_api as tradeapi
import alpaca_connection as ac

dtype=numpy.float64
alpaca_connect = ac.Alpaca_Connect()

API_KEY = alpaca_connect.key_id
SECRET_KEY = alpaca_connect.secret_key
API_URL = alpaca_connect.endpoint

connection = sqlite3.connect(alpaca_connect.db_path)

connection.row_factory = sqlite3.Row

cursor = connection.cursor()

cursor.execute("""
    SELECT id, symbol, name FROM stock
""")

rows = cursor.fetchall()

symbols = []
stock_dict = {}

for row in rows:
    symbol = row['symbol']
    symbols.append(symbol)
    stock_dict[symbol] = row['id']

api = tradeapi.REST(API_KEY, SECRET_KEY, base_url=API_URL)

symbols = ['MSFT']
chunk_size = 200
for i in range(0, len(symbols), chunk_size):
    symbol_chunk = symbols[i:i + chunk_size]
    barsets = api.get_barset(symbol_chunk, 'day')

    for symbol in barsets:
        print(f"processing symbol {symbol}")

        print(barsets[symbol])

        recent_closes = [bar.c for bar in barsets[symbol]]
        if len(recent_closes) >= 50:
            print(numpy.array(recent_closes))

            sma_20 = tulipy.sma(numpy.array(recent_closes), period=20)
            sma_50 = tulipy.sma(numpy.array(recent_closes), period=500)
            print(f"{sma_20} & {sma_50}")


        for bar in barsets[symbol]:
            stock_id = stock_dict[symbol]
    #         cursor.execute("""
    #             INSERT INTO stock_price (stock_id, date, open, high, low, close, volume, sma_20, sma_50, rsi_14)
    #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    #         """, (stock_id, bar.t.date(), bar.o, bar.h, bar.l, bar.c, bar.v, sma_20, sma50, rsi_14))

connection.commit()
