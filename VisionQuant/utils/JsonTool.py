import pandas as pd
import numpy as np


def getdata_from_json(jsdata, orient='records', **kwargs):
    # jsstr = bytes.decode(jsdata, encoding="utf-8")
    df = pd.read_json(jsdata, orient=orient, **kwargs)
    return df


def to_json(dfdata, orient='records'):
    jsdata = dfdata.to_json(orient=orient)
    return jsdata
