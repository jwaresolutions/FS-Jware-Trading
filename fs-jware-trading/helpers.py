from datetime import date, datetime
from pytz import timezone


def get_dst_isoformat(_date=date.today().isoformat()):
    tz = timezone('America/New_York')
    _date = datetime.strptime(f'{_date}', '%Y-%m-%d').astimezone(tz)
    _date = _date.isoformat()
    return _date[-6:]

def timenow_isoformat():
    return datetime.now()


