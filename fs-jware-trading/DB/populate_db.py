import sqlite3
from API import alpaca_connection as ac
import alpaca_trade_api as tradeapi


alpaca_connect = ac.Alpaca_Connect()
API_KEY = alpaca_connect.key_id
SECRET_KEY = alpaca_connect.secret_key
API_URL = alpaca_connect.endpoint
connection_path = alpaca_connect.db_path

print(f"{API_KEY}, {SECRET_KEY}, {API_URL}")
connection = sqlite3.connect(connection_path)
connection.row_factory = sqlite3.Row

cursor = connection.cursor()

api = tradeapi.REST(
    API_KEY,
    SECRET_KEY,
    base_url=API_URL
)  # or use ENV Vars shown below
assets = api.list_assets()

cursor.execute("""
    SELECT symbol, name FROM stock
""")
rows = cursor.fetchall()
symbols = [row["symbol"] for row in rows]

for asset in assets:
    try:
        if asset.status == 'active' and asset.tradable and asset.symbol not in symbols:
            print(f"Added a new stock {asset.symbol} {asset.name}")
            cursor.execute("INSERT INTO stock (symbol, name, exchange, shortable) VALUES (?, ?, ?, ?)",
                           (asset.symbol, asset.name, asset.exchange, asset.shortable))
    except Exception as e:
        print(asset.symbol)
        print(e)

strategies = ['opening_range_break_out_down', 'Bollinger_bands']

for strategy in strategies:
    cursor.execute("""
        INSERT INTO strategy (name) VALUES (?)
    """, (strategy,))

connection.commit()
