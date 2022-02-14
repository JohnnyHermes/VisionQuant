import numpy as np
import pandas as pd

from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, CustomJS, DataRange1d, RadioButtonGroup, TableColumn, \
    DataTable, Span, Button, Label, Select, TextInput, NumeralTickFormatter, WheelZoomTool, ResetTool, \
    PanTool, CheckboxGroup, Paragraph, Title, DatePicker, RadioGroup, BoxAnnotation, FixedTicker
from bokeh.io import curdoc
from bokeh.models import HoverTool, CrosshairTool
# 导入颜色模块
# 在notebook中创建绘图空间
from bokeh.palettes import Set2_8, RdYlGn8
from bokeh.plotting import figure
from bokeh import events
import bokeh

from VisionQuant.DataCenter.CodePool import AshareCodePool
from VisionQuant.utils import TimeTool
from VisionQuant.DataCenter.DataFetch import DataSource
from VisionQuant.Analysis.Relativity.Relativity import Relativity
from VisionQuant.utils.Params import Market

analyze_data_source = DataSource.Local.VQapi

from bokeh.models import BasicTicker, ColorBar, LinearColorMapper, PrintfTickFormatter
from bokeh.plotting import figure, show

UNIT_WIDTH = 60
UNIT_HEIGHT = 60


def get_blocks_score_data(market=Market.Ashare):
    sk = analyze_data_source.sk_client().init_socket()
    res_data = analyze_data_source.fetch_blocks_score_data(sk, market=market)
    return res_data


data = get_blocks_score_data()
data = data[data['category'] == '按行业分类'][['time', 'name', 'score']]
last_time = np.max(data['time'])
last_data = data[data['time'] == last_time].sort_values(by='score', axis=0, inplace=False)
y_range = list(last_data.name)
for name in y_range:
    tmp_data = data[data['name'] == name]['score'].reset_index(drop=True)
    data[data['name'] == name].loc['score'] = tmp_data.rolling(window=3, min_periods=1).mean()
data = data[data['time'] >= sorted(set(data.time))[-81]]
x_range = sorted(list(set(data.time)))

MAP_HEIGHT = UNIT_HEIGHT * len(y_range)
MAP_WIDTH = UNIT_WIDTH * len(x_range)
# reshape to 1D array or rates with a month and year for each row.
# this is the colormap from the original NYTimes plot
colors = ["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41"]
mapper = LinearColorMapper(palette=colors, low=16, high=112)
TOOLS = "save,reset"

p = figure(title="result",
           x_range=x_range, y_range=y_range,
           plot_height=MAP_HEIGHT, plot_width=MAP_WIDTH+50,
           x_axis_location="above",
           tools=TOOLS, toolbar_location='above')

p.grid.grid_line_color = None
p.axis.axis_line_color = None
p.axis.major_tick_line_color = \
    None
p.axis.major_label_text_font_size = "24px"
p.axis.major_label_standoff = 0
p.xaxis.major_label_orientation = 3.1415926 / 3

p.rect(x="time", y="name", width=1, height=1,
       source=data,
       fill_color={'field': 'score', 'transform': mapper},
       line_color=None)

# 将score 转换为整数
data['score_show'] = np.round(data['score'])
p.text(x="time", y="name", text='score_show', text_color='black',
       alpha=0.6667, text_font_size='20px', text_baseline='middle',
       text_align='center', source=data)
color_bar = ColorBar(color_mapper=mapper, major_label_text_font_size="24px",
                     ticker=FixedTicker(ticks=[0, 16, 32, 48, 64, 80, 96, 112, 128]),
                     label_standoff=6, border_line_color=None)
p.add_layout(color_bar, 'right')

show(p)
