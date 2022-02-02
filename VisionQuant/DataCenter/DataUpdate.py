#! encoding=utf-8
import time
import requests
import json
import pandas as pd
from tqdm import tqdm

from VisionQuant.DataCenter.DataServer import DataServer
from VisionQuant.DataCenter.DataStore import store_kdata_to_hdf5
from VisionQuant.DataCenter.DataFetch import DataSource
from VisionQuant.utils.Params import Market
from VisionQuant.DataCenter.CodePool import AshareCodePool
from VisionQuant.DataCenter.DataStore import store_code_list_stock, store_blocks_data

data_server = DataServer()


def get_hy_names_em() -> pd.DataFrame:
    """
    东方财富网-沪深板块-行业板块-名称
    http://quote.eastmoney.com/center/boardlist.html#industry_board
    :return: 行业板块-名称
    :rtype: pandas.DataFrame
    """
    url = "http://17.push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": "1",
        "pz": "2000",
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "m:90 t:2 f:!50",
        "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f22,f33,f11,f62,f128,f136,f115,f152,f124,f107,f104,f105,f140,f141,f207,f208,f209,f222",
        "_": "1626075887768",
    }
    r = requests.get(url, params=params)
    data_json = r.json()
    temp_df = pd.DataFrame(data_json["data"]["diff"])
    temp_df.columns = [
        '-',
        "最新价",
        "涨跌幅",
        "涨跌额",
        "-",
        "_",
        "-",
        "换手率",
        "-",
        "-",
        "-",
        "板块代码",
        "-",
        "板块名称",
        "-",
        "-",
        "-",
        "-",
        "总市值",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "上涨家数",
        "下跌家数",
        "-",
        "-",
        "-",
        "领涨股票",
        "-",
        "-",
        "领涨股票-涨跌幅",
        "-",
        "-",
        "-",
        "-",
        "-",
    ]
    temp_df = temp_df[["板块名称", "板块代码"]]
    return temp_df


def get_hy_cons_em(symbol: str = "BK0475") -> list:
    """
    东方财富网-沪深板块-行业板块-板块成份
    https://data.eastmoney.com/bkzj/BK1027.html
    :param symbol: 板块名称
    :param code: 行业代码
    :type symbol: str
    :return: 板块成份
    :rtype: pandas.DataFrame
    """
    stock_board_code = symbol
    url = "http://29.push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": "1",
        "pz": "2000",
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": f"b:{stock_board_code} f:!50",
        "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152,f45",
        "_": "1626081702127",
    }
    r = requests.get(url, params=params)
    data_json = r.json()
    temp_df = pd.DataFrame(data_json["data"]["diff"])
    temp_df.columns = [
        "_",
        "最新价",
        "涨跌幅",
        "涨跌额",
        "成交量",
        "成交额",
        "振幅",
        "换手率",
        "市盈率-动态",
        "_",
        "_",
        "代码",
        "_",
        "名称",
        "最高",
        "最低",
        "今开",
        "昨收",
        "_",
        "_",
        "_",
        "市净率",
        "_",
        "_",
        "_",
        "_",
        "_",
        "_",
        "_",
        "_",
        "_",
        "_",
    ]
    res_list = temp_df["代码"].to_list()
    return res_list


def get_gn_names_em() -> pd.DataFrame:
    """
    东方财富网-沪深板块-概念板块-名称
    http://quote.eastmoney.com/center/boardlist.html#concept_board
    :return: 概念板块-名称
    :rtype: pandas.DataFrame
    """
    url = "http://79.push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": "1",
        "pz": "2000",
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "m:90 t:3 f:!50",
        "fields": "f2,f3,f4,f8,f12,f14,f15,f16,f17,f18,f20,f21,f24,f25,f22,f33,f11,f62,f128,f124,f107,f104,f105,f136",
        "_": "1626075887768",
    }
    r = requests.get(url, params=params)
    data_json = r.json()
    temp_df = pd.DataFrame(data_json["data"]["diff"])
    temp_df.columns = [
        "最新价",
        "涨跌幅",
        "涨跌额",
        "换手率",
        "_",
        "板块代码",
        "板块名称",
        "_",
        "_",
        "_",
        "_",
        "总市值",
        "_",
        "_",
        "_",
        "_",
        "_",
        "_",
        "上涨家数",
        "下跌家数",
        "_",
        "_",
        "领涨股票",
        "_",
        "_",
        "领涨股票-涨跌幅",
    ]
    temp_df = temp_df[["板块名称", "板块代码", ]]
    return temp_df


def get_gn_cons_em(symbol: str = "BK0816") -> list:
    """
    东方财富-沪深板块-概念板块-板块成份
    http://quote.eastmoney.com/center/boardlist.html#boards-BK06551
    :param symbol: 板块代码
    :type symbol: str
    :return: 板块成份
    :rtype: pandas.DataFrame
    """
    stock_board_code = symbol
    url = "http://29.push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": "1",
        "pz": "2000",
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": f"b:{stock_board_code} f:!50",
        "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152,f45",
        "_": "1626081702127",
    }
    r = requests.get(url, params=params)
    data_json = r.json()

    temp_df = pd.DataFrame(data_json["data"]["diff"])
    temp_df.columns = [
        "_",
        "最新价",
        "涨跌幅",
        "涨跌额",
        "成交量",
        "成交额",
        "振幅",
        "换手率",
        "市盈率-动态",
        "_",
        "_",
        "代码",
        "_",
        "名称",
        "最高",
        "最低",
        "今开",
        "昨收",
        "_",
        "_",
        "_",
        "市净率",
        "_",
        "_",
        "_",
        "_",
        "_",
        "_",
        "_",
        "_",
        "_",
        "_",
    ]
    res_list = temp_df["代码"].to_list()
    return res_list


def get_all_cons_em() -> list:
    """
    东方财富网-沪深京 A 股-实时行情
    http://quote.eastmoney.com/center/gridlist.html#hs_a_board
    :return: 实时行情
    :rtype: pandas.DataFrame
    """
    url = "http://82.push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": "1",
        "pz": "5000",
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048",
        "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152",
        "_": "1623833739532",
    }
    r = requests.get(url, params=params)
    data_json = r.json()
    if not data_json["data"]["diff"]:
        return list()
    temp_df = pd.DataFrame(data_json["data"]["diff"])
    temp_df.columns = [
        "_",
        "最新价",
        "涨跌幅",
        "涨跌额",
        "成交量",
        "成交额",
        "振幅",
        "换手率",
        "市盈率-动态",
        "量比",
        "_",
        "代码",
        "_",
        "名称",
        "最高",
        "最低",
        "今开",
        "昨收",
        "_",
        "_",
        "_",
        "市净率",
        "_",
        "_",
        "_",
        "_",
        "_",
        "_",
        "_",
        "_",
        "_",
    ]
    res = temp_df["代码"].to_list()
    return res


def update_ashare_blocks():
    gn_names = get_gn_names_em()
    hy_names = get_hy_names_em()
    res = {'按行业分类': dict(), '按概念分类': dict()}
    for name, code in tqdm(zip(gn_names['板块名称'], gn_names['板块代码'])):
        res['按概念分类'][name] = get_hy_cons_em(code)
        time.sleep(0.5)

    res['按概念分类']['0沪深京A股'] = get_all_cons_em()
    time.sleep(0.5)

    for name, code in tqdm(zip(hy_names['板块名称'], hy_names['板块代码'])):
        res['按行业分类'][name] = get_hy_cons_em(code)
        time.sleep(0.5)

    return res


def update_single_stock(code):
    data_server.add_data(code)
    datastruct = data_server.update_data(code)
    store_kdata_to_hdf5(datastruct)
    data_server.remove_data(code)


if __name__ == '__main__':
    # code_pool = AshareCodePool(codelist_data_source=DataSource.Live.VQtdx)
    # # 更新A股代码列表
    # store_code_list_stock(code_pool.code_df, Market.Ashare)
    #
    # # 更新A股股票数据
    # test_code_list = code_pool.get_all_code()
    # for _code in test_code_list.values():
    #     update_single_stock(_code)
    #     print("update kdata success: {}".format(_code.code))

    # 更新板块数据
    blocks_data = update_ashare_blocks()
    store_blocks_data(blocks_data,Market.Ashare)

    print('update ok')
