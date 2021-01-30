import alpaca_connection, ssl, smtplib
from datetime import date
import alpaca_trade_api as tradeapi

alpaca_connect = alpaca_connection.Alpaca_Connect()
API_KEY = alpaca_connect.key_id
SECRET_KEY = alpaca_connect.secret_key
API_URL = alpaca_connect.endpoint
current_date = date.today().isoformat()
context = ssl.create_default_context()
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url=API_URL)

def order(symbol, side, limit_price, profit_price, stop_price):
    print("order placed")
    api.submit_order(
        symbol=symbol,
        side=side,
        type='limit',
        qty='1',
        time_in_force='day',
        order_class='bracket',
        limit_price=limit_price,
        take_profit=dict(
            limit_price=profit_price,
        ),
        stop_loss=dict(
            stop_price=stop_price,
        )
    )


def send_message(messages):
    with smtplib.SMTP_SSL(alpaca_connect.email_host, alpaca_connect.email_port, context=context) as server:
        server.login(alpaca_connect.email_address, alpaca_connect.email_password)
        email_message = f"Subject: Trade Notification for {current_date}\n\n"
        email_message += "\n\n".join(messages)
        server.sendmail(alpaca_connect.email_address, alpaca_connect.email_address, email_message)
        server.sendmail(alpaca_connect.email_address, alpaca_connect.email_sms, email_message)
