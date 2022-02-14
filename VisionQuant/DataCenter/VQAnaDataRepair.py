#! encoding=utf-8
import sys

import numpy as np
import pandas as pd
from tqdm import tqdm

from VisionQuant.DataCenter.DataServer import DataServer
from VisionQuant.DataCenter.DataFetch import DataSource, FetchDataFailed, AshareBasicDataAPI
from VisionQuant.utils.Params import Market
from VisionQuant.Analysis.Relativity.Relativity import Relativity, RELATIVITY_MAX_LEVEL
from VisionQuant.DataCenter.CodePool import AshareCodePool
from VisionQuant.DataCenter.DataStore import store_code_list_stock, store_blocks_data, \
    store_basic_finance_data, store_kdata_to_hdf5, store_update_failed_codelist, store_relativity_score_data_to_hdf5, \
    store_blocks_score_data_to_hdf5
from VisionQuant.utils import TimeTool
from VisionQuant.utils.VQlog import logger
from VisionQuant.utils.TimeTool import ASHARE_TRADE_DATE
import argparse

# 命令行参数解析
parser = argparse.ArgumentParser()
parser.add_argument('-m', "--market", help="要修复的市场,目前支持Ashare(A股)", nargs='+', default='Ashare')
parser.add_argument('-d', "--date", required=True, help="指定要修复的日期", nargs='+')
parser.add_argument('-r', "--repair", required=True, help="指定要修复的类型", nargs='+',
                    choices=['relativity', 'block_score'])
today_date = TimeTool.time_to_str(TimeTool.get_now_time(), '%Y-%m-%d')
args = parser.parse_args()

data_source = DataSource.Local.Default


def repair_relativity_data(_market, dates: list):
    logger.info("开始修复relativity data")
    sk = data_source.sk_client().init_socket()
    data = data_source.fetch_relativity_score_data(sk, market=_market)
    new_data_df = data[data['time'].apply(lambda x: x not in dates)]
    store_relativity_score_data_to_hdf5(new_data_df, market=_market, append=False)
    logger.success("修复relativity data成功!")


def repair_blocks_score_data(_market, dates: list):
    logger.info("开始修复blocks score data")
    sk = data_source.sk_client().init_socket()
    data = data_source.fetch_blocks_score_data(sk, market=_market)
    new_data_df = data[data['time'].apply(lambda x: x not in dates)]
    store_blocks_score_data_to_hdf5(new_data_df, market=_market, append=False)
    logger.success("修复blocks score data成功!")


def check_repair_dates(dates):
    for date in dates:
        if date not in ASHARE_TRADE_DATE:
            logger.trace("{} 不是A股交易日，请重新确认！程序退出...".format(date))
            return 0
    return 1


if __name__ == '__main__':
    market = args.market if isinstance(args.market, list) else [args.market]
    repair_type = args.repair if isinstance(args.repair, list) else [args.repair]
    repair_dates = args.date

    for m in market:
        if m.lower() == 'ashare':
            logger.info("{} 执行修复操作, 市场: {}".format(today_date, 'Ashare'))
            ret = check_repair_dates(repair_dates)
            if not ret:
                sys.exit()
            else:
                if 'relativity' in repair_type:
                    repair_relativity_data(Market.Ashare, repair_dates)
                if 'block_score' in repair_type:
                    repair_blocks_score_data(Market.Ashare, repair_dates)
        else:
            logger.error("输入错误的参数-m {}".format(args.market))
            raise ValueError("未知的市场参数！目前支持: Ashare")
            # todo: 多市场支持

