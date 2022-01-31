from VisionQuant.DataCenter.DataServer import DataServer
from VisionQuant.DataCenter.DataStore import store_kdata_to_hdf5
from VisionQuant.utils.Code import Code
from VisionQuant.DataCenter.DataFetch import DataSource
from VisionQuant.utils.Params import Freq, Stock
from VisionQuant.DataCenter.CodePool import get_ashare_stock_dict
from VisionQuant.DataCenter.DataStore import store_code_list_stock

data_server = DataServer()


def update_single(code):
    data_server.add_data(code)
    datastruct = data_server.update_data(code)
    store_kdata_to_hdf5(datastruct)
    data_server.remove_data(code)


if __name__ == '__main__':
    live_sk = data_server.sk_client_mng.init_socket(*DataSource.Live.VQtdx.name)
    test_stock_list = DataSource.Live.VQtdx.fetch_codelist(live_sk)
    store_code_list_stock(test_stock_list, Stock.Ashare)
    test_code_list = get_ashare_stock_dict().values()
    # test_code_list = [Code('601728', data_source={'local': DataSource.Local.Default})]
    tmp_i = 0
    """
    while tmp_i < len(test_code_list):
        if test_code_list[tmp_i].code != '605588':
            tmp_i += 1
        else:
            break
    """
    for code in test_code_list:
        update_single(code)
        print("update kdata success: {}".format(code.code))
    """
    test_datastruct = data_server.get_data(test_code)
    print(test_datastruct.get_kdata(Freq.MIN5).fliter(end=10).data)
    test_datastruct = data_server.update_data(test_code)
    print(test_datastruct.get_kdata(Freq.MIN5).fliter(start=-242).data)
    # print(test_datastruct.code.market)
    store_kdata_to_hdf5(test_datastruct)
    test_code1 = test_code.copy()
    test_code1.data_source_local = DataSource.Local.Default
    print(test_code1.data_source_local.name)
    sk = data_server.sk_client_mng.init_socket(*test_code1.data_source_local.name)
    print(test_code1.data_source_local.fetch_kdata(sk, test_code1))
    """
    print('ok')
