import time

import numpy as np
import pandas as pd
from bokeh.document import Document

from bokeh.layouts import gridplot, column, row
from bokeh.models import ColumnDataSource, CustomJS, DataRange1d, BoxSelectTool, Div, RadioButtonGroup, TableColumn, \
    DataTable, Span, Button, Label, CompositeTicker, Select, TextInput, NumeralTickFormatter, WheelZoomTool, ResetTool, \
    PanTool, CheckboxGroup, Paragraph, PolyDrawTool, PolyEditTool, Title, DatePicker, RadioGroup, LogAxis
from bokeh.themes import built_in_themes
from bokeh.io import curdoc
from bokeh.models import HoverTool, CrosshairTool
from bokeh.models.widgets import Panel, Tabs
# 导入颜色模块
# 在notebook中创建绘图空间
from bokeh.palettes import Spectral11, Set2_6, Bokeh6, Pastel1_9, Pastel2_8, Set2_8
from bokeh.plotting import figure
from bokeh import events
from bokeh.layouts import gridplot
from bokeh.plotting import show
from tqdm import tqdm
import bokeh

from VisionQuant.DataCenter.CodePool import AshareCodePool
from VisionQuant.utils import TimeTool
from VisionQuant.utils.Code import Code
import datetime
from VisionQuant.DataCenter.DataFetch import DataSource
from VisionQuant.Analysis.Relativity.Relativity import Relativity
from VisionQuant.Analysis.Relativity import relativity_cy
from VisionQuant.utils.Params import Market

curdoc().theme = 'dark_minimal'
max_level = 7
data_source = DataSource.Local.Default

score_ax: bokeh.plotting.Figure = None
show_data_class = 'score'

#  main ax parameters
MAIN_WEIGHT = 1000
MAIN_HEIGHT = 500
line_colorlist = [Set2_8[i] for i in (7, 2, 1, 0, 3, 4, 5)]
main_ax: bokeh.plotting.Figure = None
main_ax_line_source_dict = dict()
main_ax_last_price_line = None
main_ax_last_price_label: bokeh.models.Label = None
code = None
ana_result: Relativity = None
decimal_num = 2

# 价格label
pricelabel = Label(x=0, y=0, x_units='data',
                   text=str(round(0, 2)), render_mode='css', text_align='left',
                   border_line_color='black', border_line_alpha=1.0,
                   background_fill_color='white', background_fill_alpha=1.0,
                   x_offset=0, text_font_size='11pt', visible=False)


def get_analyze_data(_code):
    global ana_result, decimal_num
    strategy_obj = Relativity(code=_code, show_result=False)
    strategy_obj.analyze()
    ana_result = strategy_obj
    if ana_result.min_step - 0.001 < 1e-6:
        decimal_num = 3
    else:
        decimal_num = 2


def create_main_ax():
    global main_ax
    # tool: 十字
    crosshair = CrosshairTool(line_color='#888888')
    # tool: 滚轮缩放选矿
    x_wheel_zoom_tool = WheelZoomTool(dimensions='width', maintain_focus=False)
    x_pan_tool = PanTool(dimensions='width')
    reset_tool = ResetTool()
    main_ax = figure(plot_width=MAIN_WEIGHT, plot_height=MAIN_HEIGHT,
                     toolbar_location='above',
                     tools=[x_wheel_zoom_tool, x_pan_tool, crosshair, reset_tool],
                     active_drag=x_pan_tool,
                     active_scroll=x_wheel_zoom_tool,
                     y_axis_location='right',
                     )
    main_ax.x_range = DataRange1d(bounds=(0, ana_result.last_index + 1920), start=0, end=ana_result.last_index + 960)
    main_ax.grid.grid_line_alpha = 0.4
    main_ax.xaxis.ticker.base = 24
    main_ax.xaxis.ticker.desired_num_ticks = 4
    main_ax.xaxis.ticker.num_minor_ticks = 2
    main_ax.yaxis.major_label_standoff = 0
    main_ax.min_border_right = 50
    main_ax.yaxis.minor_tick_line_color = 'white'
    main_ax.yaxis.major_tick_line_color = 'white'
    main_ax.yaxis.formatter = NumeralTickFormatter()

    main_ax.add_layout(pricelabel)
    MouseMoveCallback = CustomJS(args={'label': pricelabel, 'x_range': main_ax.x_range, 'y_range': main_ax.y_range,
                                       'decimal_num': decimal_num},
                                 code="""
                                 label.y=cb_obj.y;
                                 label.x=x_range.end; 
                                 label.text=String(label.y.toFixed(decimal_num));
                                 if (label.y>=y_range.start && label.y<=y_range.end){
                                     label.visible=true;}
                                 else{label.visible=false;}
                                 """)
    MouseLeaveCallback = CustomJS(args={'label': pricelabel},
                                  code="""
                                  label.visible=false;
                                  """)
    MouseEnterCallback = CustomJS(args={'label': pricelabel},
                                  code="""
                                  label.visible=true;
                                  """)
    MouseWheelCallback = CustomJS(args={'label': pricelabel, 'x_range': main_ax.x_range, 'y_range': main_ax.y_range,
                                        'decimal_num': decimal_num},
                                  code="""
                                  label.y=cb_obj.y;
                                  label.x=x_range.end;
                                  label.text=String(label.y.toFixed(decimal_num));
                                  if (label.y>=y_range.start && label.y<=y_range.end){
                                      label.visible=true;}
                                  else{label.visible=false;}
                                  """)
    main_ax.js_on_event(events.MouseMove, MouseMoveCallback)
    main_ax.js_on_event(events.MouseLeave, MouseLeaveCallback)
    main_ax.js_on_event(events.MouseEnter, MouseEnterCallback)
    main_ax.js_on_event(events.MouseWheel, MouseWheelCallback)


def draw_main_ax():
    global main_ax, main_ax_line_source_dict, \
        main_ax_last_price_line, main_ax_last_price_label
    main_ax.title = Title(text="{} {}".format(code.code, TimeTool.time_to_str(ana_result.last_time)))
    main_ax.x_range.bounds = (0, ana_result.last_index + 240)
    main_ax.x_range.end = ana_result.last_index + 240
    main_ax.x_range.start = main_ax.x_range.end - 48 * 45
    points_dict = ana_result.time_grav.get_all_points()
    for level, points in points_dict.items():
        if level != 0:
            main_ax_line_source_dict[level] = ColumnDataSource(
                data={'index': points['index'][:-1], 'price': points['price'][:-1]})
            main_ax.line(x='index', y='price', source=main_ax_line_source_dict[level],
                         color=line_colorlist[level],
                         legend_label='级别{}'.format(level))
        else:
            main_ax_line_source_dict[level] = ColumnDataSource(
                data={'index': points['index'], 'price': points['price']})
            main_ax.line(x='index', y='price', source=main_ax_line_source_dict[level],
                         color=line_colorlist[level],
                         legend_label='级别{}'.format(level))

    time_list = [TimeTool.time_to_str(t, '%y-%m-%d %H:%M') for t in ana_result.kdata.data['time']]
    xaxis_label_dict = dict(zip(range(len(time_list)), time_list))
    main_ax.xaxis.major_label_overrides = xaxis_label_dict
    main_ax.legend.click_policy = "hide"
    main_ax.legend.location = "top_left"
    indices = np.where((main_ax_line_source_dict[0].data['index'] >= main_ax.x_range.start) &
                       (main_ax_line_source_dict[0].data['index'] <= main_ax.x_range.end))
    pricelist = main_ax_line_source_dict[0].data['price'][indices]
    max_price = np.max(pricelist)
    min_price = np.min(pricelist)
    pad_price = (max_price - min_price) * 0.05
    main_ax.y_range.end = round(max_price + pad_price, decimal_num)
    main_ax.y_range.start = round(min_price - pad_price, decimal_num)
    if decimal_num == 3:
        last_price_label_text_format = "{:.3f}"
        main_ax.yaxis.formatter.format = '0.000'
    else:
        last_price_label_text_format = "{:.2f}"
        main_ax.yaxis.formatter.format = '0.00'

    # 当前价格
    main_ax_last_price_label = Label(x=main_ax.x_range.end, y=ana_result.last_price, x_units='data',
                                     text=last_price_label_text_format.format(ana_result.last_price),
                                     render_mode='css', text_align='left',
                                     border_line_color='#ffffcc', border_line_alpha=1.0,
                                     background_fill_color='#ffffcc', background_fill_alpha=1.0,
                                     x_offset=0, text_font_size='11pt', text_color='black', visible=True)
    main_ax_last_price_line = Span(location=ana_result.last_price, dimension='width',
                                   line_color='#ffffcc', line_width=1, line_dash="dashed")
    main_ax.add_layout(main_ax_last_price_label)
    main_ax.add_layout(main_ax_last_price_line)

    MainAxisAutozoomCallback_start = CustomJS(
        args={'y_range': main_ax.y_range, 'data_source': main_ax_line_source_dict[0]},
        code='''
            clearTimeout(window._autoscale_timeout);
            var index = data_source.data['index'],
                price = data_source.data['price'],
                min_price = Infinity,
                max_price = -Infinity,
                start = cb_obj.start,
                end = cb_obj.end,
                low = 0,
                high = index.length-1,
                mid = Math.round((low+high) / 2),
                start_i = 0,
                end_i = 0,
                i = 0;
            while (low < high && mid != high){
                if (index[mid] < start){
                    low = mid;
                }else if(index[mid] > start) {
                    high = mid;
                }else{
                    break;
                }
                mid = Math.round((low+high) / 2);
            };
            start_i = high;
            low = 0;
            high = index.length-1;
            mid = Math.round((low+high) / 2);
            while (low < high && mid != high){
                if (index[mid] < end){
                    low = mid;
                }else if(index[mid] > end) {
                    high = mid;
                }else{
                    break;
                }
                mid = Math.round((low+high) / 2);
            };
            end_i = high;
            var new_price_list = price.slice(start_i,end_i+1);
            new_price_list.forEach((price) => {
                if (price > max_price) {
                    max_price = price;
                }
                if (price < min_price) {
                    min_price = price;
                }
            });
            var pad_price = (max_price - min_price) * 0.05;
            window._autoscale_timeout = setTimeout(function() {
                y_range.start = min_price - pad_price;
                y_range.end = max_price + pad_price;
            });
            ''')
    MainAxisAutozoomCallback_end = CustomJS(
        args={'last_price_label': main_ax_last_price_label,
              'label': pricelabel},
        code='''
                last_price_label.x = cb_obj.end;
                label.x = cb_obj.end;
                ''')
    y_range_change_callback_start = CustomJS(
        args={'last_price_label': main_ax_last_price_label},
        code='''
            if (cb_obj.start < last_price_label.y && last_price_label.y < cb_obj.end){
                last_price_label.visible = true;
            }else{
                last_price_label.visible = false;
            }
            ''')
    y_range_change_callback_end = CustomJS(
        args={'last_price_label': main_ax_last_price_label},
        code='''
            if (cb_obj.start < last_price_label.y && last_price_label.y < cb_obj.end){
                last_price_label.visible = true;
            }else{
                last_price_label.visible = false;
            }
            ''')
    ds_change_callback = CustomJS(args={'y_range': main_ax.y_range, 'x_range': main_ax.x_range},
                                  code="""
                                  clearTimeout(window._autoscale_timeout_ds);
                                var index = cb_obj.data['index'],
                                    price = cb_obj.data['price'],
                                    min_price = Infinity,
                                    max_price = -Infinity,
                                    start = x_range.start,
                                    end = x_range.end,
                                    low = 0,
                                    high = index.length-1,
                                    mid = Math.round((low+high) / 2),
                                    start_i = 0,
                                    end_i = 0,
                                    i = 0;
                                while (low < high && mid != high){
                                    if (index[mid] < start){
                                        low = mid;
                                    }else if(index[mid] > start) {
                                        high = mid;
                                    }else{
                                        break;
                                    }
                                    mid = Math.round((low+high) / 2);
                                };
                                start_i = high;
                                low = 0;
                                high = index.length-1;
                                mid = Math.round((low+high) / 2);
                                while (low < high && mid != high){
                                    if (index[mid] < end){
                                        low = mid;
                                    }else if(index[mid] > end) {
                                        high = mid;
                                    }else{
                                        break;
                                    }
                                    mid = Math.round((low+high) / 2);
                                };
                                end_i = high;
                                var new_price_list = price.slice(start_i,end_i+1);
                                new_price_list.forEach((price) => {
                                    if (price > max_price) {
                                        max_price = price;
                                    }
                                    if (price < min_price) {
                                        min_price = price;
                                    }
                                });
                                var pad_price = (max_price - min_price) * 0.05;
                                window._autoscale_timeout_ds = setTimeout(function() {
                                    y_range.start = min_price - pad_price;
                                    y_range.end = max_price + pad_price;
                                });
                                  """)
    main_ax.x_range.js_on_change('start', MainAxisAutozoomCallback_start)
    main_ax.x_range.js_on_change('end', MainAxisAutozoomCallback_end)
    main_ax.y_range.js_on_change('start', y_range_change_callback_start)
    main_ax.y_range.js_on_change('end', y_range_change_callback_end)
    main_ax_line_source_dict[0].js_on_change('data', ds_change_callback)


def get_relativity_score_data(market=Market.Ashare):
    sk = data_source.sk_client().init_socket()
    res_data = data_source.fetch_relativity_score_data(sk, market=market)
    return res_data


def get_blocks_score_data(market=Market.Ashare):
    sk = data_source.sk_client().init_socket()
    res_data = data_source.fetch_blocks_score_data(sk, market=market)
    return res_data


def get_score_details():
    global source_data
    tmp_score_data = np.array(source_data['score'])
    count_data = np.zeros(len(tmp_score_data), dtype=int)
    for i in range(max_level):
        level_score = tmp_score_data % 2
        count_data += level_score
        source_data['level_{}'.format(i)] = level_score
        tmp_score_data = tmp_score_data // 2
    source_data['rise_count'] = count_data


def df_select(data_df, key, value, sortkey=None, ascending=None):
    filtered_data = data_df[data_df[key] == value]
    if sortkey is not None:
        if isinstance(sortkey, list):
            if ascending is None:
                ascending = [False for _ in range(len(sortkey))]
        else:
            if ascending is None:
                ascending = False
        res = filtered_data.sort_values(by=sortkey, axis=0, ascending=ascending, inplace=False)  # ascending=True为升序
        return res
    else:
        return filtered_data


def date_change_callback(attr, old, new):
    datasource.data = df_select(source_data, 'time', new)
    blocks_datasource.data = df_select(blocks_source_data, 'time', new)


def blocks_datasource_selected_change_callback(attr, old, new):
    select_block_name = blocks_datasource.data['name'][new[0]]
    select_block_category = blocks_datasource.data['category'][new[0]]
    select_block_time = blocks_datasource.data['time'][new[0]]
    block_code_list = blocks_data[select_block_category][select_block_name]
    tmp_data_df = df_select(source_data, 'time', select_block_time, sortkey=['score', 'rise_count'])
    new_data_df = tmp_data_df[tmp_data_df['code'].apply(lambda x: x in block_code_list)]
    datasource.data = new_data_df
    update_score_ax(select_block_name, get_score_ax_ds(df_select(blocks_source_data, 'name', select_block_name)))


def datasource_selected_change_callback(attr, old, new):
    global code, all_code_dict
    select_name = datasource.data['name'][new[0]]
    select_code = datasource.data['code'][new[0]]
    code = all_code_dict[select_code]
    get_analyze_data(code)
    update_score_ax(select_name, get_score_ax_ds(df_select(source_data, 'code', select_code)))
    create_main_ax()
    draw_main_ax()
    layout.children[1].children[1] = main_ax


def block_category_select_callback(value):
    global block_category_select_labels
    tmp_data_df = df_select(blocks_source_data, 'time', last_time, sortkey=['score', 'rise_count'])
    if value != 0:
        label = block_category_select_labels[value]
        tmp_data_df = df_select(tmp_data_df, 'category', label)
        blocks_datasource.data = tmp_data_df
    else:
        blocks_datasource.data = tmp_data_df


def create_score_ax():
    global score_ax
    x_wheel_zoom_tool = WheelZoomTool(dimensions='width', maintain_focus=False)
    x_pan_tool = PanTool(dimensions='width')
    reset_tool = ResetTool()
    score_ax = figure(plot_width=900, plot_height=500,
                      toolbar_location='above',
                      tools=[x_pan_tool, x_wheel_zoom_tool, reset_tool],
                      active_drag=x_pan_tool,
                      active_scroll=x_wheel_zoom_tool,
                      y_axis_location='right',
                      )
    score_ax.x_range = DataRange1d()
    score_ax.grid.grid_line_alpha = 0.6
    score_ax.xaxis.ticker.base = 20
    score_ax.xaxis.ticker.desired_num_ticks = 5
    score_ax.xaxis.ticker.num_minor_ticks = 4
    score_ax.xaxis.ticker.min_interval = 1
    score_ax.yaxis.major_label_standoff = 0
    score_ax.min_border_right = 50
    score_ax.yaxis.formatter = NumeralTickFormatter(format='0.00')
    for val in (0, 2, 4, 8, 16, 32, 64, 128):
        score_ax.add_layout(Span(location=val, dimension='width',
                                 line_color='#ffffcc', line_width=1, line_dash="dashed"))
    score_ax_ds_change_callback = CustomJS(args={'y_range': score_ax.y_range, 'x_range': score_ax.x_range},
                                           code="""
                                  clearTimeout(window._autoscale_timeout_score_ax_ds);
                                var index = cb_obj.data['index'],
                                    price = cb_obj.data['value'],
                                    min_price = Infinity,
                                    max_price = -Infinity,
                                    start = x_range.start,
                                    end = x_range.end,
                                    low = 0,
                                    high = index.length-1,
                                    mid = Math.round((low+high) / 2),
                                    start_i = 0,
                                    end_i = 0,
                                    i = 0;
                                while (low < high && mid != high){
                                    if (index[mid] < start){
                                        low = mid;
                                    }else if(index[mid] > start) {
                                        high = mid;
                                    }else{
                                        break;
                                    }
                                    mid = Math.round((low+high) / 2);
                                };
                                start_i = high;
                                low = 0;
                                high = index.length-1;
                                mid = Math.round((low+high) / 2);
                                while (low < high && mid != high){
                                    if (index[mid] < end){
                                        low = mid;
                                    }else if(index[mid] > end) {
                                        high = mid;
                                    }else{
                                        break;
                                    }
                                    mid = Math.round((low+high) / 2);
                                };
                                end_i = high;
                                var new_price_list = price.slice(start_i,end_i+1);
                                new_price_list.forEach((price) => {
                                    if (price > max_price) {
                                        max_price = price;
                                    }
                                    if (price < min_price) {
                                        min_price = price;
                                    }
                                });
                                var pad_price = (max_price - min_price) * 0.05;
                                window._autoscale_timeout_score_ax_ds = setTimeout(function() {
                                    y_range.start = Math.max(min_price - pad_price,0);
                                    y_range.end = max_price + pad_price;
                                },100);
                                console.log(y_range.start,y_range.end);
                                  """)
    score_ax_ds.js_on_change('data', score_ax_ds_change_callback)
    score_ax_autozoom_callback_start = CustomJS(
        args={'y_range': score_ax.y_range, 'data_source': score_ax_ds},
        code='''
            clearTimeout(window._autoscale_timeout);
            var index = data_source.data['index'],
                price = data_source.data['value'],
                min_price = Infinity,
                max_price = -Infinity,
                start = cb_obj.start,
                end = cb_obj.end,
                low = 0,
                high = index.length-1,
                mid = Math.round((low+high) / 2),
                start_i = 0,
                end_i = 0,
                i = 0;
            while (low < high && mid != high){
                if (index[mid] < start){
                    low = mid;
                }else if(index[mid] > start) {
                    high = mid;
                }else{
                    break;
                }
                mid = Math.round((low+high) / 2);
            };
            start_i = high;
            low = 0;
            high = index.length-1;
            mid = Math.round((low+high) / 2);
            while (low < high && mid != high){
                if (index[mid] < end){
                    low = mid;
                }else if(index[mid] > end) {
                    high = mid;
                }else{
                    break;
                }
                mid = Math.round((low+high) / 2);
            };
            end_i = high;
            var new_price_list = price.slice(start_i,end_i+1);
            new_price_list.forEach((price) => {
                if (price > max_price) {
                    max_price = price;
                }
                if (price < min_price) {
                    min_price = price;
                }
            });
            var pad_price = (max_price - min_price) * 0.05;
            window._autoscale_timeout = setTimeout(function() {
                y_range.start = Math.max(min_price - pad_price, 0);
                y_range.end = max_price + pad_price;
            });
            ''')
    score_ax.x_range.js_on_change('start', score_ax_autozoom_callback_start)


def get_score_ax_ds(df_data, show_key='score'):
    res_data = dict()
    res_data['index'] = list(range(len(df_data)))
    res_data['time'] = df_data['time'].to_list()
    res_data['value'] = df_data[show_key].to_list()
    return res_data


def draw_score_ax():
    score_ax.title = Title(text="{} {}".format('沪深京A股', show_data_class))
    end_index = score_ax_ds.data['index'][len(score_ax_ds.data['index']) - 1]
    score_ax.x_range.bounds = (0, end_index)
    score_ax.x_range.start = end_index - 40
    score_ax.x_range.end = end_index
    score_ax.line(x='index', y='value', source=score_ax_ds, line_width=2)
    xaxis_label_dict = dict(zip(score_ax_ds.data['index'], score_ax_ds.data['time']))
    score_ax.xaxis.major_label_overrides = xaxis_label_dict


def update_score_ax(name, new_data):
    score_ax.title.text = "{} {}".format(name, show_data_class)
    score_ax_ds.data = new_data


source_data = get_relativity_score_data()
get_score_details()

code_pool = AshareCodePool()

blocks_data = code_pool.get_blocks_data()
blocks_source_data = get_blocks_score_data()
last_time = np.max(source_data['time'])

datasource = ColumnDataSource(df_select(source_data, 'time', last_time, sortkey=['score', 'rise_count']))
datasource.selected.on_change('indices', datasource_selected_change_callback)
score_ax_ds = ColumnDataSource(get_score_ax_ds(df_select(blocks_source_data, 'name', '0沪深京A股')))

blocks_datasource = ColumnDataSource(df_select(blocks_source_data, 'time', last_time, sortkey='score'))
blocks_datasource.selected.on_change('indices', blocks_datasource_selected_change_callback)

end_time = TimeTool.get_now_time(return_type='datetime')
start_time = end_time - datetime.timedelta(days=365 + 180)
start_time = start_time.replace(hour=9, minute=0, second=0)
all_code_dict = code_pool.get_all_code(start_time=start_time,end_time=end_time)
code = all_code_dict['999999']
get_analyze_data(code)
create_main_ax()
draw_main_ax()

enable_dates = [(d, d) for d in set(source_data['time'])]
date_picker_model = DatePicker(value=last_time, min_date=np.min(source_data['time']), max_date=last_time, width=230,
                               enabled_dates=enable_dates)
date_picker_text = Paragraph(text="日期选择器", disable_math=True, align='center')
date_picker_model.js_on_change("value", CustomJS(code="""
    console.log('date_picker: value=' + this.value, this.toString())
"""))
date_picker_model.on_change('value', date_change_callback)
date_picker = row(date_picker_text, date_picker_model)

block_category_select_labels = list(blocks_data.keys())
block_category_select_labels.insert(0, '全部')
block_category_select_text = Paragraph(text="板块分类选择", disable_math=True, align='center')
block_category_select_model = RadioGroup(labels=block_category_select_labels, active=0, inline=True, max_width=250)
block_category_select_model.on_click(block_category_select_callback)
block_category_select = row(block_category_select_text, block_category_select_model)

columns_blocks = [
    TableColumn(field="time", title="日期"),
    TableColumn(field="name", title="板块名称"),
    TableColumn(field="stk_count", title="股票总数"),
    TableColumn(field="score", title="平均得分"),
    TableColumn(field="rise_count", title="平均上升级别数"),
]

columns = [
    TableColumn(field="time", title="日期"),
    TableColumn(field="name", title="名称"),
    TableColumn(field="code", title="代码"),
    TableColumn(field="score", title="得分"),
    TableColumn(field="rise_count", title="上升级别数"),
    TableColumn(field="level_6", title="级别6"),
    TableColumn(field="level_5", title="级别5"),
    TableColumn(field="level_4", title="级别4"),
    TableColumn(field="level_3", title="级别3"),
    TableColumn(field="level_2", title="级别2"),
    TableColumn(field="level_1", title="级别1"),
    TableColumn(field="level_0", title="级别0")
]

data_table = DataTable(source=datasource, columns=columns, width=900)
blocks_data_table = DataTable(source=blocks_datasource, columns=columns_blocks, width=600)
create_score_ax()
draw_score_ax()
layout = column(row(blocks_data_table, data_table, column(date_picker, block_category_select)),
                row(score_ax, main_ax))
curdoc().add_root(layout)
# curdoc().on_session_destroyed(cleanup_session)
curdoc().title = "result"
