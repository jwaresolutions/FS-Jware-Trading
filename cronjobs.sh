#future work, automate this process with https://stackabuse.com/scheduling-jobs-with-python-crontab/
# updates list of tradeable stocks once a week on sunday night at midnight
0 0 * * 1 {path to package}/FS-Jware-Trading/bin/python {path to package}/FS-Jware-Trading/populate_db.py > output.log 2>&1
# updates previous day price history at 4am monday-friday
0 4 * * * 1-5 {path to package}/FS-Jware-Trading/bin/python {path to package}/FS-Jware-Trading/populate_prices.py > output.log 2>&1
#runs active trade stratagys every minute from 6am to 3pm monday-friday. future work to change this to a stratagy handler script for multiple stratagies
*/1 6-15 * * 1-5 {path to package}/FS-Jware-Trading/bin/python {path to package}/FS-Jware-Trading/opening_range_breakout.py > output.log 2>&1
# automaticly pull the latest deployed version of the config, this does not work right now
#0 10 * * * cd {path to package}/FS-Jware-Trading/ && git pull --rebase > output.log 2&1
