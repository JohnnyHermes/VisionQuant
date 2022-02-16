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


ori_data = get_blocks_score_data()
data = ori_data.loc[lambda df: ((df['category'] == '按概念分类') & (df['name'] == '0沪深京A股')) |
                               (df['category'] == '按行业分类'), ('time', 'name', 'score')]
data = data.reset_index(drop=True)

for name in set(data['name']):
    score_view = data.loc[lambda df: df['name'] == name, 'score']
    data.loc[lambda df: df['name'] == name, 'score'] = score_view.rolling(window=5, min_periods=1).mean()
data = data[data['time'] >= sorted(set(data.time))[-81]]
x_range = sorted(list(set(data.time)))
last_time = np.max(data['time'])
last_data = data[data['time'] == last_time].sort_values(by='score', axis=0, inplace=False)
y_range = list(last_data.name)

MAP_HEIGHT = UNIT_HEIGHT * len(y_range)
MAP_WIDTH = UNIT_WIDTH * len(x_range)
# reshape to 1D array or rates with a month and year for each row.
# this is the colormap from the original NYTimes plot
colors = ['#3f7f3e', '#4f8e4f', '#4f8e4f', '#75ad75', '#8bbc8b', '#a3cca3', '#bcdbbc', '#dcefdc',
          '#f1d7d7', '#e7bcbc', '#dda2a2', '#d28989', '#c87373', '#be5d5d', '#b44a4a', '#aa3838']
mapper = LinearColorMapper(palette=colors, low=0, high=128)
TOOLS = "save,reset"

p = figure(title="A股市场行业宽度图 {}".format(last_time),
           x_range=x_range, y_range=y_range,
           plot_height=MAP_HEIGHT, plot_width=MAP_WIDTH + 50,
           x_axis_location="above",
           y_axis_location='right',
           tools=TOOLS, toolbar_location='above')
p.title.text_font_size = '30px'
p.title.align = 'center'
p.yaxis.axis_label_text_font_style = "bold"
p.xaxis.axis_label_text_font_style = "bold"
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
                     ticker=FixedTicker(ticks=[8 * i for i in range(0, 17)]),
                     label_standoff=6, border_line_color=None)
p.add_layout(color_bar, 'left')

curdoc().add_root(p)
curdoc().title = "A股市场行业宽度图 {}".format(last_time)
