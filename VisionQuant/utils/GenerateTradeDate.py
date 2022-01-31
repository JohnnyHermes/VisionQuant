import datetime
import os
from path import Path
from VisionQuant.utils import TimeTool, Params

start_date = datetime.datetime(2022, 1, 1)
trade_dates = []
while start_date < datetime.datetime(2023, 1, 1):
    if start_date.isoweekday() in [1, 2, 3, 4, 5]:
        trade_dates.append(TimeTool.time_to_str(start_date, '%Y-%m-%d'))
    start_date = start_date + datetime.timedelta(days=1)

fpath = Path('/'.join([Params.LOCAL_DIR, 'AshareTradeDate.txt']))
with open(fpath, 'a+') as f:
    size = os.path.getsize(fpath)
    if size > 0:
        f.write(',')
    f.write(','.join(trade_dates))