from fastapi import FastAPI
import uvicorn

from VisionQuant.utils.Code import Code
from VisionQuant.utils import TimeTool, JsonTool
from VisionQuant.DataCenter.DataFetch import DataSource
from VisionQuant.utils.Params import Market
from VisionQuant.Market.HqClient import HqClient

hq_client = HqClient()

# 类似于 app = Flask(__name__)
app = FastAPI()


# 绑定路由和视图函数
@app.get("/")
async def index():
    return {"msg": "ok"}


@app.get("/kdata/")
def fetch_kdata(code: str, freq: str, market: int, st: str, et: str):
    tmp_code = Code(code=code,
                    frequency=freq,
                    market=market,
                    start_time=st,
                    end_time=et,
                    data_source={'local': DataSource.Local.Default,
                                 'live': DataSource.Live.VQtdx}
                    )
    data_struct = hq_client.get_kdata(tmp_code)
    kdata = data_struct.get_kdata(freq).data
    # 时间序列化，转换为字符串
    kdata['time'] = kdata['time'].apply(TimeTool.time_to_str, args=('%Y%m%d%H%M%S',))
    resp = JsonTool.to_json(kdata)
    return {'msg': 'success', 'data': resp}


@app.get("/codelist/")
def fetch_codelist(market: str):
    if market == 'ashare':
        sk = DataSource.Local.Default.sk_client().init_socket()
        ashare_codelist = DataSource.Local.Default.fetch_codelist(sk, market=Market.Ashare)
        resp = JsonTool.to_json(ashare_codelist)
        return {'msg': 'success', 'data': resp}
    else:
        return {'msg': 'wrong_msg'}


if __name__ == "__main__":
    # 启动服务，因为我们这个文件叫做 main.py，所以需要启动 main.py 里面的 app
    # 第一个参数 "main:app" 就表示这个含义，然后是 host 和 port 表示监听的 ip 和端口
    uvicorn.run("main:app", host="0.0.0.0", port=5555)
