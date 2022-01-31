from VisionQuant.DataCenter.DataServer import DataServer
from VisionQuant.DataCenter.DataStore import store_kdata_to_hdf5
from VisionQuant.DataCenter.DataFetch import DataSource
from VisionQuant.utils.Params import Stock
from VisionQuant.DataCenter.CodePool import AshareCodePool
from VisionQuant.DataCenter.DataStore import store_code_list_stock

data_server = DataServer()


def update_single(code):
    data_server.add_data(code)
    datastruct = data_server.update_data(code)
    store_kdata_to_hdf5(datastruct)
    data_server.remove_data(code)


if __name__ == '__main__':
    code_pool = AshareCodePool(codelist_data_source=DataSource.Live.VQtdx)
    store_code_list_stock(code_pool.code_df, Stock.Ashare)
    test_code_list = code_pool.get_all_code()

    for _code in test_code_list.values():
        update_single(_code)
        print("update kdata success: {}".format(_code.code))

    print('update ok')
