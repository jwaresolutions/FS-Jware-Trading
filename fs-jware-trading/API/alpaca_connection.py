import API.config as config
import alpaca_trade_api as tradeapi

class Alpaca_Connect:
    def __init__(self):
        self.dryrun = True
        self.endpoint = config.endpoint_dryrun
        self.key_id = config.key_id_dryrun
        self.secret_key = config.secret_key_dryrun
        self.db_path = config.db_path
        self.email_address = config.email_address
        self.email_sms = config.email_sms
        self.email_password = config.email_password
        self.email_port = config.email_port
        self.email_host = config.email_host
        self.api = ''
        self.api_setup()

    def switch_to_live(self):
        self.endpoint = config.endpoint_live
        self.key_id = config.key_id_live
        self.secret_key = config.secret_key_live
        self.api_setup()

    def api_setup(self):
        self.api = tradeapi.REST(self.key_id, self.secret_key, base_url=self.endpoint)