from datetime import date, datetime

from pytz import timezone


def get_dst_isoformat(_date=date.today().isoformat()):
    tz = timezone('America/New_York')
    _date = datetime.strptime(f'{_date}', '%Y-%m-%d').astimezone(tz)
    _date = _date.isoformat()
    return _date[-6:]


def timenow_isoformat():
    return datetime.now().date()


def do_orders_exist():
    orders = ac.api.list_orders(status='all', after=f"{current_date}T13:30:00Z")
