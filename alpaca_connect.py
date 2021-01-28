import sys, pytz, config
from datetime import datetime

sys.path.insert(0, '/Users/malojust/PycharmProjects/FS-Jware-Trading/support_files/')


class Alpaca_Connect:
    def __init__(self):
        self.dryrun = True
        self.endpoint_dryrun = config.endpoint_dryrun
        self.key_id_dryrun = config.key_id_dryrun
        self.secret_key_dryrun = config.secret_key_dryrun

        # live accounts
        self.endpoint_live = config.endpoint_live
        self.key_id_live = config.key_id_live
        self.secret_key_live = config.secret_key_live

        # DB connection
        self.db_path = config.db_path

        # e-mail settings
        self.email_address = config.email_address
        self.email_sms = config.email_sms
        self.email_password = config.email_password
        self.email_port = config.email_port
        self.email_host = config.email_host
        self.get_keys()

    def get_keys(self):
        if self.dryrun:
            self.key_id = self.key_id_dryrun
            self.secret_key = self.secret_key_dryrun
            self.endpoint = self.endpoint_dryrun
        else:
            self.key_id = self.key_id_dryrun_live
            self.secret_key = self.secret_key_live
            self.endpoint = self.endpoint_live

    def is_dst(self):
        """Determine whether or not Daylight Savings Time (DST)
        is currently in effect"""

        x = datetime(datetime.now().year, 1, 1, 0, 0, 0, tzinfo=pytz.timezone('US/Eastern'))  # Jan 1 of this year
        y = datetime.now(pytz.timezone('US/Eastern'))

        # if DST is in effect, their offsets will be different
        return not (y.utcoffset() == x.utcoffset())
