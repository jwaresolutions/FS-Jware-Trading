import sqlite3
import config as config
import alpaca_trade_api as tradeapi

API_KEY = config.get_keys(request='key_id', dryrun=False)
SECRET_KEY = config.get_keys(request='secret_key', dryrun=False)
API_URL = config.get_keys(request='endpoint', dryrun=False)

connection = sqlite3.connect(config.db_path)
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

connection.commit()
