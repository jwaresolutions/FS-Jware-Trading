import ssl, smtplib
from time import sleep

import API.alpaca_connection as alpaca_connection
from datetime import date
import alpaca_trade_api as tradeapi


alpaca_connect = alpaca_connection.Alpaca_Connect()
API_KEY = alpaca_connect.key_id
SECRET_KEY = alpaca_connect.secret_key
API_URL = alpaca_connect.endpoint
current_date = date.today().isoformat()
context = ssl.create_default_context()
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url=API_URL)


def process_limits(symbol):
    # get account information from API
    account = api.get_account()

    # Get cash information
    cash = float(account.cash)


    # Get symbol information
    quote = api.get_last_quote(symbol)
    ask_price = float(quote.askprice)
    print(ask_price)

    #calculate bid to spend no more than 1% of capital or over 5k
    one_percent = cash / 0.01
    if one_percent < 5000:
        max_bid_amount = one_percent
    else:
        max_bid_amount = 5000

    return max_bid_amount


def send_message(messages):
    with smtplib.SMTP_SSL(alpaca_connect.email_host, alpaca_connect.email_port, context=context) as server:
        server.login(alpaca_connect.email_address, alpaca_connect.email_password)
        email_message = f"Subject: Trade Notification for {current_date}\n\n"
        email_message += "\n\n".join(messages)
        server.sendmail(alpaca_connect.email_address, alpaca_connect.email_address, email_message)
        server.sendmail(alpaca_connect.email_address, alpaca_connect.email_sms, email_message)

def fractional_order(symbol, spend):
    order_complete = False
    quote = api.get_last_quote(symbol)
    ask_price = float(quote.askprice)
    while True:
        positions = api.list_positions()
        if order_complete == False:
            order_complete = True
            print(f"buying {spend} {ask_price}")
            api.submit_order(
                symbol=symbol,
                side='buy',
                type='market',
                qty=int(spend/ask_price),
                time_in_force='day',
                stop_loss=dict(
                    stop_price=str(ask_price/0.20),
                )
            )
            sleep(5)
        else:
            try:
                if positions[0].symbol == symbol:
                    api.submit_order(
                        symbol=symbol,
                        side='sell',
                        type='market',
                        qty=positions[0].qty,
                        trail_percent='15',
                        time_in_force='day',
                        stop_loss=dict(
                            stop_price=str(ask_price / 0.20),
                        )
                    )
                    break
            except:
                pass