import datetime
import configparser
import os
from path import Path

# 读取配置文件
rootpath = Path(Path(Path(__file__).parent).parent).parent
cfg = configparser.ConfigParser()
cfg.read(rootpath + '/settings.cfg')

cfg_set_list = []


def set_cfg(section, option):
    cfg_set_list.append((section, option))


def get_cfg(section, option):
    data = cfg.get(section, option)
    return data


def write_cfg():
    while len(cfg_set_list) > 0:
        cfg.set(*cfg_set_list.pop(0))
