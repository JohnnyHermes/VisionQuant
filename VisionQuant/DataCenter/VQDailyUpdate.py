#! encoding=utf-8
import sys
import numpy as np
import pandas as pd
from tqdm import tqdm

from VisionQuant.DataCenter.DataServer import DataServer
from VisionQuant.DataCenter.DataFetch import DataSource, FetchDataFailed, AshareBasicDataAPI
from VisionQuant.utils.Params import MarketType, Freq
from VisionQuant.Analysis.Relativity.Relativity import Relativity, RELATIVITY_MAX_LEVEL
from VisionQuant.DataCenter.CodePool import AshareCodePool, FutureCodePool
from VisionQuant.DataCenter.DataStore import store_code_list, store_blocks_data, \
    store_basic_finance_data, store_kdata_to_hdf5, store_update_failed_codelist, store_relativity_score_data_to_hdf5, \
    store_blocks_score_data_to_hdf5
from VisionQuant.utils import TimeTool
from VisionQuant.utils.VQlog import logger
import argparse

# 命令行参数解析
parser = argparse.ArgumentParser()
parser.add_argument('-f', "--force_update", help="不考虑是否为交易日，强制更新数据",
                    action="store_true")
parser.add_argument('-m', "--market", help="要更新的市场,目前支持Ashare(A股)", nargs='+', default='Ashare')
parser.add_argument('-c', "--code", help="指定要更新的股票代码，主要用于修复数据", nargs='+')
parser.add_argument('-d', "--date", help="指定要分析的日期，主要用于修复分析数据，仅在level=analyze时生效", nargs='+')
parser.add_argument("-u", "--update", help="要更新的数据", default='all', nargs='+',
                    choices=['basic', 'kdata', 'analyze', 'relativity', 'blocks_score', 'all'])
parser.add_argument("--frequency", help="要更新的k线数据周期", default='1', nargs='+',
                    choices=['1', '5', 'd'])
args = parser.parse_args()

today_date = TimeTool.time_to_str(TimeTool.get_now_time(), '%Y-%m-%d')

data_server = DataServer(force_live=True)

UPDATE_MATKETTYPE = (MarketType.Ashare.SH.STOCK, MarketType.Ashare.SH.KCB, MarketType.Ashare.SH.INDEX,
                     MarketType.Ashare.SZ.STOCK, MarketType.Ashare.SZ.CYB, MarketType.Ashare.SZ.INDEX)


class DataUpdateBase:
    def __init__(self):
        self.market_name = None
        self.update_type = None
        self.update_codes = None
        self.local_ds = None
        self.live_ds = None
        self.code_pool = None
        self.analyze_date = None
        self.update_frequency = None

    def config_update_type(self, level):
        self.update_type = level

    def config_codes(self, codes):
        self.update_codes = codes

    def config_analyze_date(self, dates):
        self.analyze_date = dates

    def config_update_frequency(self, _update_frequency):
        self.update_frequency = _update_frequency

    def update(self):
        pass

    def _update_basic_data(self):
        pass

    def _update_kdata(self):
        pass

    def _update_analyze_data(self):
        pass


class AshareDataUpdate(DataUpdateBase):
    def __init__(self):
        super().__init__()
        self.market_name = 'Ashare'
        self.local_ds = DataSource.Local.Default
        self.live_ds = DataSource.Live.VQtdx
        self.code_pool = AshareCodePool(codelist_data_source=self.live_ds)

    def update(self):
        if 'all' in self.update_type:
            self._update_basic_data()
            self._update_kdata()
            self._update_analyze_data()
        else:
            if 'basic' in self.update_type:
                self._update_basic_data()
            if 'kdata' in self.update_type:
                self._update_kdata()
            if 'analyze' in self.update_type:
                self._update_analyze_data()
            else:
                if 'relativity' in self.update_type:
                    self._update_relativity_analyze_data()
                if 'blocks_score' in self.update_type:
                    self._update_blocks_score_data()

    def _update_basic_data(self):
        self._update_codelist()
        self._update_basic_finance_data()
        self._update_blocks_data()

    def _update_kdata(self):
        def update_single_stock(_code):
            try:
                datastruct = data_server.get_kdata(_code)
            except Exception as e:
                raise e
            else:
                store_kdata_to_hdf5(datastruct)

        logger.info("开始更新 {} 的A股k线数据...".format(today_date))
        if self.update_codes is not None:
            code_list = []
            for code in self.update_codes:
                code_list.append(self.code_pool.get_code(code, frequency=self.update_frequency))
        else:
            code_list = self.code_pool.get_all_code(frequency=self.update_frequency, return_type=list,
                                                    selected_market=UPDATE_MATKETTYPE)
        error_code_list = []
        code_list = tqdm(code_list)
        for code in code_list:
            code_list.set_description("Updating {} {}".format(code.code, today_date))
            try:
                update_single_stock(code)
            except Exception as e:
                print(e)
                error_code_list.append(code.code)
        if len(error_code_list) > 0:
            logger.warning("更新 {} 的A股k线数据部分成功，失败的代码列表见update_failed_codelist.txt".format(today_date))
            store_update_failed_codelist(error_code_list, today_date)
        else:
            logger.success("更新 {} 的A股k线数据成功!".format(today_date))

    def _update_analyze_data(self):
        self._update_relativity_analyze_data()
        self._update_blocks_score_data()

    def _update_relativity_analyze_data(self):
        def analyze_single_stock(_code):
            datastruct = data_server.get_kdata(_code)
            basic_finan_data = data_server.get_basic_financial_data(_code)
            strategy = Relativity(code=_code, local_data=datastruct, local_basic_finance_data=basic_finan_data)
            score = strategy.analyze_score()
            if score is not None:
                return {'time': TimeTool.time_to_str(_code.end_time, '%Y-%m-%d'),
                        'code': _code.code,
                        'name': _code.name,
                        'score': score}
            else:
                return None

        for _date in self.analyze_date:
            if _date not in TimeTool.ASHARE_TRADE_DATE:
                print("{} 不是A股交易日，将跳过...".format(_date))
                continue
            logger.info("开始更新 {} 的Relativity Analyze数据...".format(_date))
            tmp_end_time = TimeTool.str_to_dt(_date + ' 15:00:00')
            tmp_start_time = TimeTool.get_start_time(tmp_end_time, days=365 + 180)
            if self.update_codes is not None:
                tmp_code_list = self.code_pool.get_code(self.update_codes,
                                                        start_time=tmp_start_time, end_time=tmp_end_time).values()
            else:
                tmp_code_list = self.code_pool.get_all_code(return_type=list,
                                                            start_time=tmp_start_time, end_time=tmp_end_time)
            code_list = []
            for code in tmp_code_list:
                if code.market in (MarketType.Ashare.SH.STOCK, MarketType.Ashare.SZ.STOCK,
                                   MarketType.Ashare.SH.KCB, MarketType.Ashare.SZ.CYB):
                    code_list.append(code)
            code_list = tqdm(code_list)
            records_list = []
            for code in code_list:
                code_list.set_description("Analyzing {} {}".format(code.code, _date))
                try:
                    res = analyze_single_stock(code)
                    if res is not None:
                        records_list.append(res)
                except Exception as e:
                    logger.error("Relativity分析 {} {} 时出现错误，详细信息: {}{}".format(_date, code.code, e.__class__, e))

            result_df = pd.DataFrame.from_records(records_list)
            store_relativity_score_data_to_hdf5(result_df, market=MarketType.Ashare)
            logger.success("更新 {} 的Relativity Analyze数据成功!".format(_date))

    def _update_blocks_score_data(self):
        def analyze_single_date(_date):
            new_data_df = data_df[data_df['time'] == _date].reset_index(drop=True)
            tmp_score_data = np.array(new_data_df['score'])
            count_data = np.zeros(len(tmp_score_data), dtype=int)
            for i in range(RELATIVITY_MAX_LEVEL):
                level_score = tmp_score_data % 2
                count_data += level_score
                tmp_score_data = tmp_score_data // 2
            new_data_df['rise_count'] = count_data
            res_list = []
            res_item_template = {'category': '', 'time': '', 'name': '', 'stk_count': 0, 'score': 0, 'rise_count': 0}
            for category, _data in blocks_data.items():
                for block_name, code_list in tqdm(_data.items()):
                    res_item = res_item_template.copy()
                    tmp_data_df = new_data_df[new_data_df['code'].apply(lambda x: x in code_list)]
                    if len(tmp_data_df) > 0:
                        res_item['category'] = category
                        res_item['time'] = _date
                        res_item['name'] = block_name
                        res_item['stk_count'] = len(tmp_data_df)
                        res_item['score'] = tmp_data_df['score'].mean()
                        res_item['rise_count'] = tmp_data_df['rise_count'].mean()
                        res_list.append(res_item)

            res_df = pd.DataFrame.from_records(res_list)
            res_df['score'] = np.round(res_df['score'], 3)
            res_df['rise_count'] = np.round(res_df['rise_count'], 3)
            return res_df

        logger.info("开始更新A股blocks_score数据")
        try:
            blocks_data = self.code_pool.get_blocks_data()
            sk = self.local_ds.sk_client().init_socket()
            data_df = self.local_ds.fetch_relativity_score_data(sk, market=MarketType.Ashare)
        except Exception as e:
            logger.error("预读取数据失败，详细信息: {}{}".format(e.__class__, e))
        else:
            for d in self.analyze_date:
                res = analyze_single_date(d)
                store_blocks_score_data_to_hdf5(res, market=MarketType.Ashare)
                logger.success("更新 {} A股blocks_score数据成功!".format(d))

    @staticmethod
    def _update_blocks_data():
        logger.info("开始更新A股板块数据")
        try:
            res_dict = AshareBasicDataAPI.get_ashare_blocks_data()
        except FetchDataFailed:
            logger.error("获取A股板块数据失败! 详细信息见日志文件")
        else:
            try:
                store_blocks_data(res_dict, MarketType.Ashare)
            except Exception as e:
                logger.error("储存A股板块数据失败! 详细信息: {}{}".format(e.__class__, e))
            else:
                logger.success("更新A股板块数据成功!")

    def _update_codelist(self):
        logger.info("开始更新A股股票列表数据")
        try:
            self.code_pool.get_code_df()
        except RuntimeError:
            logger.error("获取A股股票列表数据失败! 详细信息见日志文件")
        else:
            try:
                store_code_list(self.code_pool.code_df, MarketType.Ashare)
            except Exception as e:
                logger.error("储存A股股票列表数据失败! 详细信息: {}{}".format(e.__class__, e))
            else:
                logger.success("更新A股股票列表数据成功!")

    @staticmethod
    def _update_basic_finance_data():
        logger.info("开始更新A股basic_finance数据")
        try:
            res_df = AshareBasicDataAPI.get_basic_finance_data()
        except FetchDataFailed:
            logger.error("获取A股basic_finance数据失败! 详细信息见日志文件")
        else:
            try:
                store_basic_finance_data(res_df, MarketType.Ashare)
            except Exception as e:
                logger.error("储存A股basic_finance数据失败! 详细信息: {}{}".format(e.__class__, e))
            else:
                logger.success("更新A股basic_finance数据成功!")


class FutureDataUpdate(DataUpdateBase):
    def __init__(self):
        super().__init__()
        self.market_name = 'Future'
        self.local_ds = DataSource.Local.Default
        self.live_ds = DataSource.Live.VQtdx_Ext
        self.code_pool = FutureCodePool(codelist_data_source=self.local_ds)

    def update(self):
        if 'all' in self.update_type:
            self._update_basic_data()
            self._update_kdata()
            self._update_analyze_data()
        else:
            if 'basic' in self.update_type:
                self._update_basic_data()
            if 'kdata' in self.update_type:
                self._update_kdata()
            if 'analyze' in self.update_type:
                self._update_analyze_data()
            else:
                if 'relativity' in self.update_type:
                    self._update_relativity_analyze_data()
                if 'blocks_score' in self.update_type:
                    self._update_blocks_score_data()

    def _update_basic_data(self):
        self._update_codelist()
        self._update_basic_finance_data()
        self._update_blocks_data()

    def _update_kdata(self):
        def update_single_stock(_code):
            try:
                datastruct = data_server.get_kdata(_code)
            except Exception as e:
                raise e
            else:
                store_kdata_to_hdf5(datastruct)

        logger.info("开始更新 {} 的A股k线数据...".format(today_date))
        if self.update_codes is not None:
            code_list = []
            for code in self.update_codes:
                code_list.append(self.code_pool.get_code(code, frequency=self.update_frequency))
        else:
            code_list = self.code_pool.get_all_code(frequency=self.update_frequency, return_type=list)
        error_code_list = []
        code_list = tqdm(code_list)
        for code in code_list:
            code_list.set_description("Updating {} {}".format(code.code, today_date))
            try:
                update_single_stock(code)
            except Exception as e:
                print(e)
                error_code_list.append(code.code)
        if len(error_code_list) > 0:
            logger.warning("更新 {} 的期货k线数据部分成功，失败的代码列表见update_failed_codelist.txt".format(today_date))
            store_update_failed_codelist(error_code_list, today_date)
        else:
            logger.success("更新 {} 的期货k线数据成功!".format(today_date))

    def _update_analyze_data(self):
        self._update_relativity_analyze_data()
        self._update_blocks_score_data()

    def _update_relativity_analyze_data(self):
        pass

    def _update_blocks_score_data(self):
        pass

    @staticmethod
    def _update_blocks_data():
        pass

    def _update_codelist(self):
        pass

    @staticmethod
    def _update_basic_finance_data():
        pass

def config_update_obj(_update_obj: DataUpdateBase, _update_type: list, codes, analyze_date, _update_frequency):
    _update_obj.config_update_type(_update_type)
    _update_obj.config_codes(codes)
    _update_obj.config_analyze_date(analyze_date)
    _update_obj.config_update_frequency(_update_frequency)


if __name__ == '__main__':
    update_obj_list = []
    market = args.market if isinstance(args.market, list) else [args.market]
    update_type = args.update if isinstance(args.update, list) else [args.update]
    update_frequencys = args.frequency if isinstance(args.frequency, list) else [args.frequency]
    if args.code is None:
        update_code = None
    else:
        update_code = args.code if isinstance(args.code, list) else [args.code]
    if args.date is None:
        update_dates = [today_date]
    else:
        update_dates = args.date

    for m in market:
        if m.lower() == 'ashare':
            if not args.force_update and TimeTool.ASHARE_TRADE_DATE is not None:
                if today_date not in TimeTool.ASHARE_TRADE_DATE:
                    logger.info("{} 不是A股交易日，不更新数据".format(today_date))
                    sys.exit()
            if args.force_update:
                logger.info("日期: {}, 对A股市场强制更新数据".format(today_date))
            else:
                logger.info("{} 是A股交易日，开始更新数据".format(today_date))
            tmp_obj = AshareDataUpdate()
            config_update_obj(tmp_obj, update_type, update_code, update_dates, update_frequencys)
            update_obj_list.append(tmp_obj)
        elif m.lower() == 'future':
            if not args.force_update and TimeTool.ASHARE_TRADE_DATE is not None:
                if today_date not in TimeTool.ASHARE_TRADE_DATE:
                    logger.info("{} 不是交易日，不更新数据".format(today_date))
                    sys.exit()
            if args.force_update:
                logger.info("日期: {}, 对期货市场强制更新数据".format(today_date))
            else:
                logger.info("{} 是交易日，开始更新数据".format(today_date))
            tmp_obj = FutureDataUpdate()
            config_update_obj(tmp_obj, update_type, update_code, update_dates, update_frequencys)
            update_obj_list.append(tmp_obj)
        else:
            logger.error("输入错误的参数-m {}".format(args.market))
            raise ValueError("未知的市场参数！目前支持: Ashare")
            # todo: 多市场支持

    for update_obj in update_obj_list:
        update_obj.update()
