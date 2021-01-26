import config as config
import sqlite3
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from datetime import date

current_date = date.today().isoformat()
app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/")
def index(request: Request):
    connection = sqlite3.connect(config.db_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    stock_filter = request.query_params.get('filter', False)

    if stock_filter == 'new_intraday_highs':
        cursor.execute("""
        SELECT id, symbol, name FROM stock ORDER by symbol
        """)
    elif stock_filter == 'new_closing_highs':
        cursor.execute("""
        SELECT * FROM(
            SELECT symbol, name stock_id, max(close), date 
            FROM stock_price JOIN stock on stock.id = stock_price.stock_id
            GROUP BY stock_id
            ORDER BY symbol
        ) WHERE date = ?
        """, (current_date,))
    elif stock_filter == 'new_intraday_lows':
        cursor.execute("""
        SELECT id, symbol, name FROM stock ORDER by symbol
        """)
    elif stock_filter == 'new_closing_lows':
        cursor.execute("""
        SELECT * FROM(
            SELECT symbol, name stock_id, min(close), date 
            FROM stock_price JOIN stock on stock.id = stock_price.stock_id
            GROUP BY stock_id
            ORDER BY symbol
        ) WHERE date = ?
        """, (current_date,))
    else:
        cursor.execute("""
        SELECT id, symbol, name FROM stock ORDER by symbol
        """)

    rows = cursor.fetchall()
    return templates.TemplateResponse("index.html", {"request": request, "stocks": rows})


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
        FROM stock JOIN stock_strategy on stock_strategy.stock_id = stock_id
        WHERE strategy_id = ?
    """, (strategy_id,))

    stocks = cursor.fetchall()

    return templates.TemplateResponse("strategy.html", {"request": request, "stocks": stocks, "strategy": strategy})