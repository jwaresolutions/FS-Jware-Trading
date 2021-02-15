import config as config
import sqlite3
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from datetime import date
import alpaca_trade_api as tradeapi
from API import alpaca_connection

alpaca_connect = alpaca_connection.Alpaca_Connect()
API_KEY = alpaca_connect.key_id
SECRET_KEY = alpaca_connect.secret_key
API_URL = alpaca_connect.endpoint

current_date = date.today().isoformat()
app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/")
def index(request: Request):
    connection = sqlite3.connect(config.db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    stock_filter = request.query_params.get('filter', False)

    if stock_filter == 'new_closing_highs':
        cursor.execute("""
        SELECT * FROM(
            SELECT symbol, name stock_id, max(close), date 
            FROM stock_price JOIN stock on stock.id = stock_price.stock_id
            GROUP BY stock_id
            ORDER BY symbol
        ) WHERE date = (select max(date) from stock_price) 
        """)
    elif stock_filter == 'new_closing_lows':
        cursor.execute("""
        SELECT * FROM(
            SELECT symbol, name stock_id, min(close), date 
            FROM stock_price JOIN stock on stock.id = stock_price.stock_id
            GROUP BY stock_id
            ORDER BY symbol
        ) WHERE date = (select max(date) from stock_price) 
        """)
    else:
        cursor.execute("""
        SELECT id, symbol, name as stock_id FROM stock ORDER by symbol
        """)

    rows = cursor.fetchall()

    cursor.execute("""
        SELECT symbol, rsi_14, sma_20, sma_50, close
        from stock_price 
        JOIN stock on stock.id = stock_price.stock_id
        WHERE date = ?
    """, (current_date,))

    indicator_rows = cursor.fetchall()
    indicator_values = {}

    for row in indicator_rows:
        indicator_values[row['symbol']] = row

    print(indicator_values)

    return templates.TemplateResponse("index.html",
                                      {"request": request,
                                       "indicator_values": indicator_values,
                                       "stocks": rows})


@app.get("/stock/{symbol}")
def stock_detail(request: Request, symbol):
    connection = sqlite3.connect(config.db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * from strategy

    """)
    strategys = cursor.fetchall()

    cursor.execute("""
        SELECT id, symbol, name FROM stock WHERE symbol = ?
    """, (symbol,))

    row = cursor.fetchone()

    cursor.execute("""
        SELECT * FROM stock_price WHERE stock_id = ? ORDER BY date DESC 
    """, (row['id'],))

    prices = cursor.fetchall()

    return templates.TemplateResponse("stock_detail.html",
                                      {"request": request, "stock": row, "bars": prices, "strategys": strategys})


@app.post("/apply_strategy")
def apply_strategy(strategy_id: int = Form(...), stock_id: int = Form(...)):
    connection = sqlite3.connect(config.db_path)
    cursor = connection.cursor()

    cursor.execute("""
    INSERT INTO stock_strategy (stock_id, strategy_id) VALUES (?, ?)
""", (stock_id, strategy_id))

    connection.commit()
    return RedirectResponse(url=f"/strategy/{strategy_id}", status_code=303)


@app.get("/strategies")
def strategies(request: Request):
    connection = sqlite3.connect(config.db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * from strategy
    """)

    strategies = cursor.fetchall()

    return templates.TemplateResponse("strategies.html", {"request": request, "strategies": strategies})


@app.get("/strategy/{strategy_id}")
def strategy(request: Request, strategy_id):
    connection = sqlite3.connect(config.db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
    SELECT id, name
    FROM strategy
    WHERE id = ?    
""", (strategy_id,))

    strategy = cursor.fetchone()

    cursor.execute("""
        SELECT symbol, name
        FROM stock_strategy
        JOIN stock on stock.id = stock_strategy.stock_id
        WHERE strategy_id = ?
""", (strategy_id,))

    stocks = cursor.fetchall()

    return templates.TemplateResponse("strategy.html", {"request": request, "stocks": stocks, "strategy": strategy})


@app.get("/orders")
def orders(request: Request):
    api = tradeapi.REST(API_KEY, SECRET_KEY, base_url=API_URL)
    orders = api.list_orders(status='all')

    return templates.TemplateResponse("orders.html", {"request": request, "orders": orders})
