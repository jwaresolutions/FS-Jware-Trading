import config, sqlite3
import alpaca_trade_api as tradeapi

API_KEY = config.get_keys(request='key_id')
SECRET_KEY = config.get_keys(request='secret_key')
API_URL = config.get_keys(request='endpoint')

connection = sqlite3.connect(config.db_path)

connection.row_factory = sqlite3.Row

cursor = connection.cursor()

cursor.execute("""
    SELECT symbol, name FROM stock
""")

rows = cursor.fetchall()

symbols = [row['symbol'] for row in rows]

api = tradeapi.REST(API_KEY, SECRET_KEY, base_url=API_URL)
assets = api.list_assets()

for asset in assets:
    try:
        if asset.status == 'active' and asset.tradable and asset.symbol not in symbols:
            print(f"Added a new stock {asset.symbol} {asset.name}")
            cursor.execute("INSERT INTO stock (symbol, name) VALUES (?, ?)", (asset.symbol, asset.name))
    except Exception as e:
        print(asset.symbol)
        print(e)

connection.commit()
