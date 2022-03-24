import json
from path import Path
from VisionQuant.utils.Params import LOCAL_DIR

record_data: dict = dict()

fname = 'VisualizeDrawing.json'
fpath = Path('/'.join([LOCAL_DIR, 'Web', fname]))
if fpath.exists():
    with open(fpath, 'r') as f:
        record_data = json.load(f)


def get_drawing(code: str):
    if record_data and code in record_data.keys():
        return record_data[code]
    else:
        return None


def store_drawing(res_dict):
    code_str = res_dict['code']
    record_data[code_str] = res_dict['data']
    with open(fpath, 'w+') as file:
        json.dump(record_data, file, indent=4)
