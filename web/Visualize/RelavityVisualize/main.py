import copy

import bokeh.plotting
import numpy as np

from bokeh.layouts import gridplot, column, row
from bokeh.models import ColumnDataSource, CustomJS, DataRange1d, BoxSelectTool, RadioButtonGroup, \
    Span, Button, Label, Select, TextInput, NumeralTickFormatter, WheelZoomTool, ResetTool, \
    PanTool, CheckboxGroup, Paragraph, PolyDrawTool, Title, BoxAnnotation
from bokeh.io import curdoc
from bokeh.models import CrosshairTool
from bokeh.palettes import Set2_8
from bokeh.plotting import figure
from bokeh import events

from VisionQuant.utils import TimeTool
from VisionQuant.utils.Code import Code
from VisionQuant.DataCenter.DataFetch import DEFAULT_ASHARE_DATA_SOURCE
from VisionQuant.Analysis.Relativity.Relativity import Relativity, ANALYZE_FREQ
from VisionQuant.Analysis.Relativity import relativity_cy
import Draw


curdoc().theme = 'dark_minimal'
MAIN_WEIGHT = 1700
MAIN_HEIGHT = 750
line_colorlist = [Set2_8[i] for i in (7, 2, 1, 0, 3, 4, 5)]
default_indicator_name = '均线离散度'
time_count = 0
auto_fresh_period = 6  # 单位：秒
period_callback_id = None

code: Code
ana_result: Relativity
decimal_num = 2

#  main ax parameters
main_ax: bokeh.plotting.Figure
main_ax_line_source_dict = dict()
main_ax_line_dict = dict()
base_points: bokeh.models.GlyphRenderer
main_ax_peak_pricelabel_list = []
main_ax_peak_span_list = []
main_ax_last_price_line = None
main_ax_last_price_label: bokeh.models.Label
main_ax_trend_source = None

#  space_grav ax parameters
space_grav_ax: bokeh.plotting.Figure
space_grav_ax_hbar: bokeh.models.GlyphRenderer
space_grav_ax_line: bokeh.models.GlyphRenderer
space_grav_dist_source: bokeh.models.ColumnDataSource
avg_cost_line = None
val_vah_box = None

#  time_grav ax parameters
time_grav_ax: bokeh.plotting.Figure
time_grav_dist_source: bokeh.models.sources.ColumnDataSource
time_grav_ax_glyphs = []

tool_ax = None
layout: bokeh.models.layouts.LayoutDOM = None

update_space_grav_dist_callback = None
update_func_lock = 0

# 价格label
pricelabel = Label(x=0, y=0, x_units='data',
                   text=str(round(0, 2)), render_mode='css', text_align='left',
                   border_line_color='black', border_line_alpha=1.0,
                   background_fill_color='white', background_fill_alpha=1.0,
                   x_offset=0, text_font_size='11pt', visible=False)

# tool: indicator选框
indicator_select: bokeh.models.widgets.Select

# tool: 筹码计算模式选择
space_grav_calc_mode = RadioButtonGroup(labels=['无', '正常', '累加'], active=0, height=30, width=190)

# tool: 代码输入框
code_input = TextInput(value="", placeholder="输入代码", height=30, width=70)

# tool: 刷新按钮
refresh_button = Button(label="刷新", button_type="success", height=30, width=50)
save_button = Button(label="保存", button_type="success", height=30, width=50)

# tool: 十字
crosshair = CrosshairTool(line_color='#888888')

# tool: box选框
select_tool = BoxSelectTool(dimensions='width', select_every_mousemove=True)

auto_refresh_checkbox = CheckboxGroup(labels=['自动刷新'], height=15, width=60)
message_show = Paragraph(text="状态:分析完成", height=15, width=110, disable_math=True)

# tool: 滚轮缩放选矿
x_wheel_zoom_tool = WheelZoomTool(dimensions='width', maintain_focus=False)
x_pan_tool = PanTool(dimensions='width')

reset_tool = ResetTool()

multi_line_source = ColumnDataSource(data={'xs': [], 'ys': []})
TOOLS = [x_pan_tool, x_wheel_zoom_tool, reset_tool, select_tool, crosshair]


def get_analyze_data(_code):
    global ana_result, decimal_num
    strategy_obj = Relativity(code=_code, show_result=False)
    strategy_obj.analyze()
    if strategy_obj.analyze_flag:
        ana_result = strategy_obj
        # 获取过去保存的画笔
        drawing_data = copy.deepcopy(Draw.get_drawing(_code.code))
        if drawing_data:
            time_series = [TimeTool.time_to_str(t) for t in ana_result.kdata.data['time']]
            try:
                new_index = time_series.index(drawing_data['save_time']['time'])
                offset = new_index - drawing_data['save_time']['index']
            except ValueError:
                print("未找到时间")
                offset = 0
            for line_x in drawing_data['line_data']['xs']:
                line_x[0] += offset
                line_x[1] += offset
            multi_line_source.data = drawing_data['line_data']
        else:
            multi_line_source.data = {}
        # 确认decimal_num
        if ana_result.min_step - 0.001 < 1e-6:
            decimal_num = 3
        else:
            decimal_num = 2
        return 1
    else:
        return 0


def configure_update_data(old_data, new_data: dict):
    patch = dict()
    stream = dict()
    keys = list(new_data.keys())
    length = len(old_data[keys[0]])
    new_length = len(new_data[keys[0]])
    for key in keys:
        if new_length > length:
            index = np.where(old_data[key] != new_data[key][:length])[0]
        else:
            index = np.where(old_data[key] != new_data[key])[0]
        if index.size > 0:
            new_value = new_data[key][index]
            patch[key] = [(int(i), v) for i, v in zip(index, new_value)]  # index元素是np.int64类型，不转换会报错
    if new_length > length:
        for key in keys:
            stream[key] = new_data[key][length:]
    return patch, stream


def create_main_ax():
    global main_ax, multi_line_source
    main_ax = figure(plot_width=MAIN_WEIGHT, plot_height=MAIN_HEIGHT,
                     toolbar_location='above',
                     tools=TOOLS,
                     active_drag=x_pan_tool,
                     active_scroll=x_wheel_zoom_tool,
                     y_axis_location='right',
                     lod_threshold=1000,
                     lod_factor=50,
                     lod_interval=250
                     )
    main_ax.x_range = DataRange1d(bounds=(0, ana_result.last_index + 1920), start=0, end=ana_result.last_index + 960)
    main_ax.grid.grid_line_alpha = 0.4
    main_ax.xaxis.ticker.base = 24
    main_ax.xaxis.ticker.desired_num_ticks = 8
    main_ax.xaxis.ticker.num_minor_ticks = 4
    # main_ax.xaxis.ticker.min_interval = 1
    main_ax.yaxis.major_label_standoff = 0
    main_ax.min_border_right = 50
    main_ax.yaxis.minor_tick_line_color = 'white'
    main_ax.yaxis.major_tick_line_color = 'white'
    main_ax.yaxis.formatter = NumeralTickFormatter()
    main_ax.ygrid.visible = False

    main_ax.add_layout(pricelabel)
    multi_line = main_ax.multi_line('xs', 'ys', source=multi_line_source, line_color='white', line_width=1.5)
    polydraw_tool = PolyDrawTool(renderers=[multi_line])
    main_ax.add_tools(polydraw_tool)
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
    main_ax.x_range.on_change('start', x_range_start_changed_callback)


def draw_main_ax(x_range=None):
    global main_ax, main_ax_line_source_dict, main_ax_line_dict, base_points, main_ax_trend_source, \
        main_ax_peak_pricelabel_list, main_ax_peak_span_list, main_ax_last_price_line, main_ax_last_price_label
    main_ax.title = Title(text="{} {}".format(code.code, TimeTool.time_to_str(ana_result.last_time)))
    main_ax.x_range.bounds = (0, ana_result.last_index + 1920)
    main_ax_peak_pricelabel_list = []
    main_ax_peak_span_list = []
    if x_range is None:
        main_ax.x_range.end = ana_result.last_index + 960
        main_ax.x_range.start = 0
    else:
        main_ax.x_range.end = x_range[1]
        main_ax.x_range.start = x_range[0]
    points_dict = ana_result.time_grav.get_all_points()
    for level, points in points_dict.items():
        if level != 0:
            main_ax_line_source_dict[level] = ColumnDataSource(
                data={'index': points['index'][:-1], 'price': points['price'][:-1]})
            main_ax.line(x='index', y='price', source=main_ax_line_source_dict[level],
                         color=line_colorlist[level],
                         legend_label='级别{}'.format(level))
            # main_ax_line_dict[level] = main_ax.line(x='index', y='price', source=main_ax_line_source_dict[level],
            #                                         color=line_colorlist[level],
            #                                         legend_label='级别{}'.format(level))
        else:
            main_ax_line_source_dict[level] = ColumnDataSource(
                data={'index': points['index'], 'price': points['price']})
            main_ax.line(x='index', y='price', source=main_ax_line_source_dict[level],
                         color=line_colorlist[level],
                         legend_label='级别{}'.format(level))
            # main_ax_line_dict[level] = main_ax.line(x='index', y='price', source=main_ax_line_source_dict[level],
            #                                         color=line_colorlist[level],
            #                                         legend_label='级别{}'.format(level))
            base_points = main_ax.scatter(x='index', y='price', source=main_ax_line_source_dict[level], alpha=0, size=1)

    main_ax_trend_source = ColumnDataSource(data=ana_result.trend_dict)
    main_ax.line(x='index', y='short', source=main_ax_trend_source, color='white',
                 line_width=2, legend_label='趋势线', visible=False)
    main_ax.line(x='index', y='mid', source=main_ax_trend_source, color='yellow',
                 line_width=2, legend_label='趋势线', visible=False)
    main_ax.line(x='index', y='long', source=main_ax_trend_source, color='violet',
                 line_width=2, legend_label='趋势线', visible=False)

    indices = np.where((main_ax_line_source_dict[0].data['index'] >= main_ax.x_range.start) &
                       (main_ax_line_source_dict[0].data['index'] <= main_ax.x_range.end))
    pricelist = main_ax_line_source_dict[0].data['price'][indices]
    max_price = np.max(pricelist)
    min_price = np.min(pricelist)
    pad_price = (max_price - min_price) * 0.05
    main_ax.y_range.end = round(max_price + pad_price, decimal_num)
    main_ax.y_range.start = round(min_price - pad_price, decimal_num)

    time_list = [TimeTool.time_to_str(t, '%y-%m-%d %H:%M') for t in ana_result.kdata.data['time']]
    len_time_list = len(time_list)
    for i in range(len_time_list, ana_result.last_index + 1920):
        minutes = 5 * (i - len_time_list + 1)
        time_list.append("+{}min".format(minutes))
    xaxis_label_dict = dict(zip(range(len(time_list)), time_list))
    main_ax.xaxis.major_label_overrides = xaxis_label_dict
    main_ax.legend.click_policy = "hide"
    main_ax.legend.location = "top_left"
    if decimal_num == 3:
        main_ax_label_text_format = "{:.2f} {:.3f}"
        last_price_label_text_format = "{:.3f}"
        main_ax.yaxis.formatter.format = '0.000'
    else:
        main_ax_label_text_format = "{:.2f} {:.2f}"
        last_price_label_text_format = "{:.2f}"
        main_ax.yaxis.formatter.format = '0.00'

    # 支撑压力
    for peak in ana_result.zcyl:
        peak_pricelabel = Label(x=main_ax.x_range.end, y=peak['price'], x_units='data',
                                text=main_ax_label_text_format.format(peak['ratio'], round(peak['price'], decimal_num)),
                                render_mode='css', text_align='right',
                                border_line_color='green', border_line_alpha=1.0,
                                background_fill_color='green', background_fill_alpha=1.0,
                                x_offset=0, text_font_size='9pt', text_color='#eeeeee', visible=False)
        peak_span = Span(location=peak['price'], dimension='width',
                         line_color='green', line_width=1, line_dash="dashed")
        if main_ax.y_range.start <= peak['price'] <= main_ax.y_range.end:
            peak_pricelabel.visible = True
        if peak['price'] < ana_result.last_price:
            peak_pricelabel.border_line_color = 'red'
            peak_pricelabel.background_fill_color = 'red'
            peak_span.line_color = 'red'
        main_ax_peak_pricelabel_list.append(peak_pricelabel)
        main_ax_peak_span_list.append(peak_span)
        main_ax.add_layout(peak_pricelabel)
        main_ax.add_layout(peak_span)

    # 当前价格
    main_ax_last_price_label = Label(x=main_ax.x_range.end, y=ana_result.last_price, x_units='data',
                                     text=last_price_label_text_format.format(ana_result.last_price),
                                     render_mode='css', text_align='right',
                                     border_line_color='#ffffcc', border_line_alpha=1.0,
                                     background_fill_color='#ffffcc', background_fill_alpha=1.0,
                                     x_offset=0, text_font_size='9pt', text_color='black', visible=False)
    if main_ax.y_range.start <= ana_result.last_price <= main_ax.y_range.end:
        main_ax_last_price_label.visible = True
    main_ax_last_price_line = Span(location=ana_result.last_price, dimension='width',
                                   line_color='#ffffcc', line_width=1, line_dash="dashed")
    main_ax.add_layout(main_ax_last_price_label)
    main_ax.add_layout(main_ax_last_price_line)

    MainAxisAutozoomCallback_end = CustomJS(
        args={'label_list': main_ax_peak_pricelabel_list, 'last_price_label': main_ax_last_price_label,
              'label': pricelabel},
        code='''
                last_price_label.x = cb_obj.end;
                label.x = cb_obj.end;
                label_list.forEach((_label) => {
                    _label.x=cb_obj.end; 
                });
                ''')
    y_range_change_callback_start = CustomJS(
        args={'label_list': main_ax_peak_pricelabel_list, 'last_price_label': main_ax_last_price_label},
        code='''
            label_list.forEach((_label) => {
                if (cb_obj.start < _label.y && _label.y < cb_obj.end){
                    _label.visible = true;
                }else{
                    _label.visible = false;
                }
            });
            if (cb_obj.start < last_price_label.y && last_price_label.y < cb_obj.end){
                last_price_label.visible = true;
            }else{
                last_price_label.visible = false;
            }
            ''')
    y_range_change_callback_end = CustomJS(
        args={'label_list': main_ax_peak_pricelabel_list, 'last_price_label': main_ax_last_price_label},
        code='''
            label_list.forEach((_label) => {
                if (cb_obj.start < _label.y && _label.y < cb_obj.end){
                    _label.visible = true;
                }else{
                    _label.visible = false;
                }
            });
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
                                if ((min_price != Infinity) && (max_price != -Infinity) && (min_price != max_price)){
                                window._autoscale_timeout_ds = setTimeout(function() {
                                    y_range.start = min_price - pad_price;
                                    y_range.end = max_price + pad_price;
                                });
                                }
                                  """)
    # main_ax.x_range.js_on_change('start', MainAxisAutozoomCallback_start)
    main_ax.x_range.js_on_change('end', MainAxisAutozoomCallback_end)
    main_ax.y_range.js_on_change('start', y_range_change_callback_start)
    main_ax.y_range.js_on_change('end', y_range_change_callback_end)
    main_ax_line_source_dict[0].js_on_change('data', ds_change_callback)


def update_main_ax():
    global main_ax, code, ana_result, main_ax_last_price_label
    main_ax.title.text = "{} {}".format(code.code, TimeTool.time_to_str(ana_result.last_time))
    if decimal_num == 3:
        main_ax_label_text_format = "{:.2f} {:.3f}"
        last_price_label_text_format = "{:.3f}"
        main_ax.yaxis.formatter.format = '0.000'
    else:
        main_ax_label_text_format = "{:.2f} {:.2f}"
        last_price_label_text_format = "{:.2f}"
        main_ax.yaxis.formatter.format = '0.00'
    points_dict = ana_result.time_grav.get_all_points()
    for level, points in points_dict.items():
        if level != 0:
            new_data = {'index': points['index'][:-1], 'price': points['price'][:-1]}
            patch, stream = configure_update_data(main_ax_line_source_dict[level].data, new_data)
            if patch:
                main_ax_line_source_dict[level].patch(patch)
            if stream:
                main_ax_line_source_dict[level].stream(stream)
            # main_ax_line_source_dict[level].data = new_data
            # main_ax_line_dict[level].data_source.data = new_data
        else:
            new_data = {'index': points['index'], 'price': points['price']}
            patch, stream = configure_update_data(main_ax_line_source_dict[level].data, new_data)
            # print(main_ax_line_source_dict[level].data['index'][-2:], main_ax_line_source_dict[level].data['price'][-2:])
            # print(patch)
            # print(stream)
            if patch:
                main_ax_line_source_dict[level].patch(patch)
                # base_points.data_source.patch(patch)
            if stream:
                main_ax_line_source_dict[level].stream(stream)
                # base_points.data_source.stream(stream)
            # main_ax_line_source_dict[level].data = new_data
            # main_ax_line_dict[level].data_source.data = new_data
            # base_points.data_source.data = new_data
    main_ax_trend_source.data = ana_result.trend_dict
    indices = np.where((main_ax_line_source_dict[0].data['index'] >= main_ax.x_range.start) &
                       (main_ax_line_source_dict[0].data['index'] <= main_ax.x_range.end))
    pricelist = main_ax_line_source_dict[0].data['price'][indices]
    max_price = np.max(pricelist)
    min_price = np.min(pricelist)
    pad_price = (max_price - min_price) * 0.05
    y_range_end = round(max_price + pad_price, decimal_num)
    y_range_start = round(min_price - pad_price, decimal_num)

    # 当前价格
    main_ax_last_price_label.update(text=last_price_label_text_format.format(ana_result.last_price),
                                    y=ana_result.last_price)
    main_ax_last_price_line.location = ana_result.last_price

    time_list = [TimeTool.time_to_str(t, '%y-%m-%d %H:%M') for t in ana_result.kdata.data['time']]
    len_time_list = len(time_list)
    for i in range(len_time_list, ana_result.last_index + 1920):
        minutes = 5 * (i - len_time_list + 1)
        time_list.append("+{}min".format(minutes))
    xaxis_label_dict = dict(zip(range(len(time_list)), time_list))
    main_ax.xaxis.major_label_overrides = xaxis_label_dict

    i = 0
    zcyl_length = len(ana_result.zcyl)
    while i < zcyl_length:
        peak = ana_result.zcyl[i]
        if i < len(main_ax_peak_pricelabel_list):
            main_ax_peak_pricelabel_list[i].update(y=peak['price'],
                                                   text=main_ax_label_text_format.format(
                                                       peak['ratio'], round(peak['price'], decimal_num)))
            main_ax_peak_span_list[i].location = peak['price']
            main_ax_peak_pricelabel_list[i].visible = y_range_start < peak['price'] < y_range_end
            if peak['price'] < ana_result.last_price:
                main_ax_peak_pricelabel_list[i].border_line_color = 'red'
                main_ax_peak_pricelabel_list[i].background_fill_color = 'red'
                main_ax_peak_span_list[i].line_color = 'red'
            else:
                main_ax_peak_pricelabel_list[i].border_line_color = 'green'
                main_ax_peak_pricelabel_list[i].background_fill_color = 'green'
                main_ax_peak_span_list[i].line_color = 'green'
        else:
            peak_pricelabel = Label(x=main_ax.x_range.end, y=peak['price'], x_units='data',
                                    text=main_ax_label_text_format.format(peak['ratio'],
                                                                          round(peak['price'], decimal_num)),
                                    render_mode='css', text_align='right',
                                    border_line_color='green', border_line_alpha=1.0,
                                    background_fill_color='green', background_fill_alpha=1.0,
                                    x_offset=0, text_font_size='9pt', text_color='#eeeeee', visible=False)
            peak_span = Span(location=peak['price'], dimension='width',
                             line_color='green', line_width=1, line_dash="dashed", visible=False)
            peak_pricelabel.visible = y_range_start < peak['price'] < y_range_end
            if peak['price'] < ana_result.last_price:
                peak_pricelabel.border_line_color = 'red'
                peak_pricelabel.background_fill_color = 'red'
                peak_span.line_color = 'red'
            main_ax_peak_pricelabel_list.append(peak_pricelabel)
            main_ax_peak_span_list.append(peak_span)
            main_ax.add_layout(peak_pricelabel)
            main_ax.add_layout(peak_span)
        i += 1
    while i < len(main_ax_peak_pricelabel_list):
        main_ax_peak_pricelabel_list[i].visible = False
        main_ax_peak_span_list[i].visible = False
        i += 1


def create_time_grav_ax():
    global time_grav_ax, time_grav_dist_source
    time_grav_ax = figure(plot_width=MAIN_WEIGHT, plot_height=165,  # 图表宽度、高度
                          toolbar_location=None,
                          x_range=main_ax.x_range,
                          y_axis_location='right',
                          active_drag=None,
                          lod_threshold=1000,
                          lod_factor=50,
                          lod_interval=250
                          )
    time_grav_ax.y_range.only_visible = True
    time_grav_ax.xaxis.visible = False
    time_grav_ax.grid.grid_line_alpha = 0.4
    time_grav_ax.xaxis.ticker.base = 24
    time_grav_ax.xaxis.ticker.desired_num_ticks = 8
    time_grav_ax.xaxis.ticker.num_minor_ticks = 4
    time_grav_ax.xaxis.ticker.min_interval = 1
    time_grav_ax.yaxis.major_label_standoff = 0
    time_grav_ax.min_border_right = 50
    time_grav_dist_source = ColumnDataSource()


def configure_time_grav_ax_yrange(data_dict, start=None, end=None, is_mvol=False):
    global time_grav_ax
    indices = np.where((data_dict['index'] >= time_grav_ax.x_range.start) &
                       (data_dict['index'] <= time_grav_ax.x_range.end))
    if indices:
        max_val = None
        min_val = None
        for key, data in data_dict.items():
            if key != 'index':
                tmp_data = data[indices]
                tmp_max_val = np.max(tmp_data)
                if is_mvol:
                    tmp_min_val = np.min(tmp_data[np.where(tmp_data > 1e-6)])
                else:
                    tmp_min_val = np.min(tmp_data)
                if max_val is None:
                    max_val = tmp_max_val
                elif tmp_max_val > max_val:
                    max_val = tmp_max_val
                if min_val is None:
                    min_val = tmp_min_val
                elif tmp_min_val < min_val:
                    min_val = tmp_min_val
        pad_val = (max_val - min_val) * 0.05
        if start is not None:
            time_grav_ax.y_range.start = start
        else:
            time_grav_ax.y_range.start = min_val - pad_val
        if end is not None:
            time_grav_ax.y_range.end = end
        else:
            time_grav_ax.y_range.end = max_val + pad_val


def draw_time_grav_dist_mvol(indicator):
    global time_grav_ax, time_grav_dist_source
    time_grav_ax.yaxis.formatter = NumeralTickFormatter(format='0.00a')
    index = (2 * indicator['val']['index'] - indicator['val']['width']) / 2
    buyvol = np.sqrt(indicator['val']['buyvol'])
    sellvol = np.sqrt(indicator['val']['sellvol'])
    # allvol = np.sqrt(indicator['val']['allvol'])
    # new_data = {'index': index, 'buyvol': buyvol, 'sellvol': sellvol, 'allvol': allvol}
    new_data = {'index': index, 'buyvol': buyvol, 'sellvol': sellvol}
    time_grav_dist_source.data = new_data
    # time_grav_ax.line(x='index', y='allvol', source=time_grav_dist_source,
    #                   color='#eeeeee', line_alpha=0.6)
    time_grav_ax.circle(x='index', y='buyvol', source=time_grav_dist_source,
                        color='red')
    time_grav_ax.circle(x='index', y='sellvol', source=time_grav_dist_source,
                        color='green')
    configure_time_grav_ax_yrange(new_data, is_mvol=True)


def update_time_grav_dist_mvol(indicator):
    global time_grav_dist_source
    index = (2 * indicator['val']['index'] - indicator['val']['width']) / 2
    buyvol = np.sqrt(indicator['val']['buyvol'])
    sellvol = np.sqrt(indicator['val']['sellvol'])
    # allvol = np.sqrt(indicator['val']['allvol'])
    # new_data = {'index': index, 'buyvol': buyvol, 'sellvol': sellvol, 'allvol': allvol}
    new_data = {'index': index, 'buyvol': buyvol, 'sellvol': sellvol}
    patch, stream = configure_update_data(time_grav_dist_source.data, new_data)
    if patch:
        time_grav_dist_source.patch(patch)
    if stream:
        time_grav_dist_source.stream(stream)
    configure_time_grav_ax_yrange(time_grav_dist_source.data)


def draw_time_grav_dist_lsd(indicator):
    global time_grav_ax, time_grav_dist_source
    time_grav_ax.yaxis.formatter = NumeralTickFormatter(format='0.0000')
    index = indicator['val']['index']
    short = indicator['val']['short'] * 100
    long = indicator['val']['long'] * 100
    all_lisandu = indicator['val']['all'] * 100
    new_data = {'index': index, 'short': short, 'long': long, 'all': all_lisandu}
    time_grav_dist_source.data = new_data
    time_grav_ax.line(x='index', y='short', source=time_grav_dist_source,
                      color='white', legend_label='short')
    time_grav_ax.line(x='index', y='long', source=time_grav_dist_source,
                      color='yellow', legend_label='long')
    time_grav_ax.line(x='index', y='all', source=time_grav_dist_source,
                      color='violet', legend_label='all')
    time_grav_ax.legend.location = "top_left"
    configure_time_grav_ax_yrange(time_grav_dist_source.data, start=0)


def x_range_start_changed_callback(attr, old, new):
    indices = np.where((main_ax_line_source_dict[0].data['index'] >= main_ax.x_range.start) &
                       (main_ax_line_source_dict[0].data['index'] <= main_ax.x_range.end))
    if indices:
        pricelist = main_ax_line_source_dict[0].data['price'][indices]
        max_price = np.max(pricelist)
        min_price = np.min(pricelist)
        pad_price = (max_price - min_price) * 0.05
        main_ax.y_range.end = round(max_price + pad_price, decimal_num)
        main_ax.y_range.start = round(min_price - pad_price, decimal_num)
        if indicator_select.value == "均线离散度":
            configure_time_grav_ax_yrange(time_grav_dist_source.data, start=0)
        elif "平均成交量" in indicator_select.value:
            configure_time_grav_ax_yrange(time_grav_dist_source.data, is_mvol=True)
        elif indicator_select.value in ('MTM', 'Trend'):
            configure_time_grav_ax_yrange(time_grav_dist_source.data)


def draw_time_grav_dist_mtm(indicator):
    global time_grav_ax, time_grav_dist_source
    time_grav_ax.yaxis.formatter = NumeralTickFormatter(format='0.000')
    time_grav_dist_source.data = indicator['val']
    time_grav_ax.line(x='index', y='short', source=time_grav_dist_source,
                      color='white', legend_label='short')
    time_grav_ax.line(x='index', y='mid', source=time_grav_dist_source,
                      color='yellow', legend_label='mid')
    time_grav_ax.line(x='index', y='long', source=time_grav_dist_source,
                      color='violet', legend_label='long')
    time_grav_ax.legend.location = "top_left"
    configure_time_grav_ax_yrange(indicator['val'])


def draw_time_grav_dist_trend(indicator):
    global time_grav_ax, time_grav_dist_source
    time_grav_ax.yaxis.formatter = NumeralTickFormatter(format='0.000')
    time_grav_dist_source.data = indicator['val']
    time_grav_ax.line(x='index', y='short', source=time_grav_dist_source,
                      color='white', legend_label='short')
    time_grav_ax.line(x='index', y='long', source=time_grav_dist_source,
                      color='yellow', legend_label='long')
    time_grav_ax.legend.location = "top_left"
    configure_time_grav_ax_yrange(indicator['val'])


def update_time_grav_dist_lsd(indicator):
    global time_grav_ax_glyphs, time_grav_dist_source
    index = indicator['val']['index']
    short = indicator['val']['short'] * 100
    long = indicator['val']['long'] * 100
    all_lisandu = indicator['val']['all'] * 100
    new_data = {'index': index, 'short': short, 'long': long, 'all': all_lisandu}
    patch, stream = configure_update_data(time_grav_dist_source.data, new_data)
    if patch:
        time_grav_dist_source.patch(patch)
    if stream:
        time_grav_dist_source.stream(stream)
    configure_time_grav_ax_yrange(time_grav_dist_source.data, start=0)


def update_time_grav_dist_mtm(indicator):
    global time_grav_dist_source
    patch, stream = configure_update_data(time_grav_dist_source.data, indicator['val'])
    if patch:
        time_grav_dist_source.patch(patch)
    if stream:
        time_grav_dist_source.stream(stream)
    configure_time_grav_ax_yrange(time_grav_dist_source.data)


def update_time_grav_dist_trend(indicator):
    global time_grav_dist_source
    patch, stream = configure_update_data(time_grav_dist_source.data, indicator['val'])
    if patch:
        time_grav_dist_source.patch(patch)
    if stream:
        time_grav_dist_source.stream(stream)
    configure_time_grav_ax_yrange(time_grav_dist_source.data)


def draw_time_grav_dist():
    indicators_list = ana_result.indicators
    for indicator in indicators_list:
        if indicator['name'] == default_indicator_name:
            draw_time_grav_dist_lsd(indicator)


def indicator_select_callback(_, old, new):
    global ana_result, time_grav_ax
    indicators_list = ana_result.indicators
    create_time_grav_ax()
    for indicator in indicators_list:
        if indicator['name'] == new:
            if "平均成交量" in indicator['name']:
                draw_time_grav_dist_mvol(indicator)
            elif indicator['name'] == "均线离散度":
                draw_time_grav_dist_lsd(indicator)
            elif indicator['name'] == 'MTM':
                draw_time_grav_dist_mtm(indicator)
            elif indicator['name'] == 'Trend':
                draw_time_grav_dist_trend(indicator)
            break
    layout.children[2] = (time_grav_ax, 1, 0)


def update_time_grav_dist():
    global ana_result, time_grav_ax
    indicators_list = ana_result.indicators
    for indicator in indicators_list:
        if indicator['name'] == indicator_select.value:
            if indicator_select.value == "均线离散度":
                update_time_grav_dist_lsd(indicator)
            elif "平均成交量" in indicator_select.value:
                update_time_grav_dist_mvol(indicator)
            elif indicator_select.value == 'MTM':
                update_time_grav_dist_mtm(indicator)
            elif indicator_select.value == 'Trend':
                update_time_grav_dist_trend(indicator)


def create_space_grav_ax():
    global space_grav_ax
    space_grav_ax = figure(plot_width=200, plot_height=MAIN_HEIGHT,  # 图表宽度、高度
                           toolbar_location=None,
                           x_range=DataRange1d(bounds=(0, 1.02),
                                               start=0, end=1.02),
                           y_range=main_ax.y_range,
                           active_drag=None
                           )
    space_grav_ax.yaxis.major_label_text_alpha = 0
    space_grav_ax.margin = (0, 0, 0, 0)  # top、right、bottom、left margin
    main_ax.ygrid.visible = False


def calc_space_grav_dist(end_index, start_index=0):
    if start_index == 0:
        tmp_grav_dist = ana_result.space_grav.get_grav_dist(end_index)
        tmp_grav_dist['volume'] /= max(np.max(tmp_grav_dist['volume']), 1)
        cdf = np.cumsum(tmp_grav_dist['volume'])
        cdf = cdf / cdf[cdf.shape[0] - 1]
    else:
        tmp_grav_dist = ana_result.space_grav.get_grav_dist(end_index, start_index=start_index)
        tmp_grav_dist['volume'] /= max(np.max(tmp_grav_dist['volume']), 1)
        cdf = np.cumsum(tmp_grav_dist['volume'])
        cdf = cdf / cdf[cdf.shape[0] - 1]
    return {'price': tmp_grav_dist['price'], 'volume': tmp_grav_dist['volume'], 'cdf': cdf}


def draw_space_grav_dist():
    global avg_cost_line, val_vah_box, space_grav_ax_hbar, space_grav_ax_line, space_grav_dist_source
    dist_data = calc_space_grav_dist(ana_result.last_index)
    space_grav_dist_source = ColumnDataSource(data=dist_data)
    height = ana_result.space_grav.step * 0.7
    space_grav_ax_hbar = space_grav_ax.hbar(left=0, right='volume', y='price', height=height, color='#6666cc',
                                            source=space_grav_dist_source)
    space_grav_ax_line = space_grav_ax.line(x='cdf', y='price', source=space_grav_dist_source, color='#eeeeee')
    avg_price = relativity_cy.get_avg_price(dist_data['price'], dist_data['volume'], 0.5)
    vah = relativity_cy.get_avg_price(dist_data['price'], dist_data['volume'], 0.8413)
    val = relativity_cy.get_avg_price(dist_data['price'], dist_data['volume'], 0.1587)
    avg_cost_line = Span(location=avg_price, dimension='width', line_color='yellow', line_width=2)
    val_vah_box = BoxAnnotation(bottom=val, top=vah, fill_alpha=0.2, fill_color='#66ccff', level="underlay")
    space_grav_ax.add_layout(val_vah_box)
    space_grav_ax.add_layout(avg_cost_line)


def update_space_grav_dist():
    global avg_cost_line, space_grav_ax_hbar, val_vah_box
    dist_data = calc_space_grav_dist(ana_result.last_index)
    space_grav_dist_source.data = dist_data
    space_grav_ax_hbar.glyph.height = ana_result.space_grav.step * 0.7
    avg_price = relativity_cy.get_avg_price(dist_data['price'], dist_data['volume'], 0.5)
    vah = relativity_cy.get_avg_price(dist_data['price'], dist_data['volume'], 0.8413)
    val = relativity_cy.get_avg_price(dist_data['price'], dist_data['volume'], 0.1587)
    avg_cost_line.location = avg_price
    val_vah_box.bottom = val
    val_vah_box.top = vah


def update_space_grav_dist_normal(event):
    if space_grav_calc_mode.active == 1:
        base_points.data_source.selected.indices = []
        tmp_end_index = event.x
        if tmp_end_index <= 1:
            tmp_end_index = 1
        elif tmp_end_index >= ana_result.last_index:
            tmp_end_index = ana_result.last_index
        else:
            tmp_end_index = round(tmp_end_index)
        new_grav_dist = calc_space_grav_dist(tmp_end_index)
        space_grav_dist_source.data = new_grav_dist
        avg_cost_line.location = relativity_cy.get_avg_price(new_grav_dist['price'], new_grav_dist['volume'], 0.5)
        vah = relativity_cy.get_avg_price(new_grav_dist['price'], new_grav_dist['volume'], 0.8413)
        val = relativity_cy.get_avg_price(new_grav_dist['price'], new_grav_dist['volume'], 0.1587)
        val_vah_box.bottom = val
        val_vah_box.top = vah


def update_space_grav_dist_sum(attr, old, new):
    if space_grav_calc_mode.active == 2:
        indices = new
        if indices:
            tmp_idx = indices[len(indices) - 1]
            end_index = base_points.data_source.data['index'][tmp_idx]
            start_index = base_points.data_source.data['index'][indices[0]]
            new_grav_dist = calc_space_grav_dist(end_index, start_index)
            space_grav_dist_source.data = new_grav_dist
            avg_cost_line.location = relativity_cy.get_avg_price(new_grav_dist['price'], new_grav_dist['volume'], 0.5)
            vah = relativity_cy.get_avg_price(new_grav_dist['price'], new_grav_dist['volume'], 0.8413)
            val = relativity_cy.get_avg_price(new_grav_dist['price'], new_grav_dist['volume'], 0.1587)
            val_vah_box.bottom = val
            val_vah_box.top = vah


def update_space_grave_dist_none():
    base_points.data_source.selected.indices = []
    new_grav_dist = calc_space_grav_dist(ana_result.last_index)
    space_grav_dist_source.data = new_grav_dist
    avg_cost_line.location = relativity_cy.get_avg_price(new_grav_dist['price'], new_grav_dist['volume'], 0.5)
    vah = relativity_cy.get_avg_price(new_grav_dist['price'], new_grav_dist['volume'], 0.8413)
    val = relativity_cy.get_avg_price(new_grav_dist['price'], new_grav_dist['volume'], 0.1587)
    val_vah_box.bottom = val
    val_vah_box.top = vah


def space_grav_calc_mode_callback(attr, old, new):
    if space_grav_calc_mode.active == 0:
        update_space_grave_dist_none()


def create_tool_ax():
    global indicator_select, tool_ax
    indicator_select = Select(title="指标", value=default_indicator_name,
                              options=[item['name'] for item in ana_result.indicators],
                              height=50, width=190)
    tool_ax = column(indicator_select, space_grav_calc_mode,
                     row(code_input, refresh_button, save_button),
                     row(message_show, auto_refresh_checkbox))


def configure_tools():
    code_input.value = code.code
    indicator_select.on_change('value', indicator_select_callback)
    space_grav_calc_mode.on_change('active', space_grav_calc_mode_callback)
    main_ax.on_event(events.MouseMove, update_space_grav_dist_normal)
    base_points.data_source.selected.on_change('indices', update_space_grav_dist_sum)
    refresh_button.js_on_click(CustomJS(args={'message_show': message_show},
                                        code="""
                                            message_show.text = "状态:正在分析";
                                        """))
    refresh_button.on_click(update)
    save_button.on_click(save_drawing)
    auto_refresh_checkbox.on_change('active', auto_refresh_callback)


def save_drawing():
    res_dict = dict()
    res_dict['code'] = code.code
    res_dict['data'] = {'save_time': {'index': int(ana_result.last_index),
                                      'time': TimeTool.time_to_str(ana_result.last_time)},
                        'line_data': dict(multi_line_source.data)}
    Draw.store_drawing(res_dict)


def refresh_button_callback():
    global update_func_lock
    if update_func_lock:
        pass
    else:
        update_func_lock = 1
        update()
        update_func_lock = 0


def update(from_auto_refresh=False):
    global code, message_show, main_ax, main_ax_line_source_dict, base_points, time_grav_ax_glyphs, ana_result, \
        time_grav_ax, avg_cost_line, space_grav_ax_hbar, start_time, end_time
    tmp_code = code.code
    if code_input.value != "":
        new_code = str(code_input.value)
    else:
        new_code = code.code
    end_time = TimeTool.get_now_time('datetime')
    start_time = TimeTool.get_start_time(end_time, days=365+365)
    try:
        code = Code(new_code, frequency=ANALYZE_FREQ, start_time=start_time, end_time=end_time)
    except Exception as e:
        print(e)
        message_show.text = "输入代码错误！"
        code_input.value = tmp_code
    else:
        tmp_start = main_ax.x_range.start
        tmp_end = main_ax.x_range.end
        tmp_data_end = ana_result.last_index
        try:
            ret = get_analyze_data(code)
            if ret == 0:
                return
        except Exception as e:
            print(e)
            message_show.text = "获取数据出错！"
        else:
            if from_auto_refresh:
                x_range_end = tmp_end
                x_range_start = tmp_start
            else:
                x_range_end = ana_result.last_index + (tmp_end - tmp_data_end)
                x_range_start = ana_result.last_index - (tmp_data_end - tmp_start)
            if tmp_code != code.code:
                create_main_ax()
                draw_main_ax(x_range=(x_range_start, x_range_end))
                create_space_grav_ax()
                draw_space_grav_dist()
                create_time_grav_ax()
                draw_time_grav_dist()
                indicator_select.value = default_indicator_name
                main_ax.on_event(events.MouseMove, update_space_grav_dist_normal)
                base_points.data_source.selected.on_change('indices', update_space_grav_dist_sum)
                layout.children[0] = (main_ax, 0, 0)
                layout.children[1] = (space_grav_ax, 0, 1)
                layout.children[2] = (time_grav_ax, 1, 0)
                curdoc().title = "Analyze - {}".format(code.code)
            else:
                update_main_ax()
                update_time_grav_dist()
                update_space_grav_dist()
            message_show.text = "状态:分析完成"


def auto_update():
    global time_count, update_func_lock
    time_count += 1
    if time_count < auto_fresh_period:
        message_show.text = "状态:{}秒后刷新".format(auto_fresh_period - time_count)
    else:
        message_show.text = "状态:正在分析"
        time_count = 0
        if update_func_lock:
            pass
        else:
            update_func_lock = 1
            update(from_auto_refresh=True)
            update_func_lock = 0


def auto_refresh_callback(attr, old, new):
    global period_callback_id, time_count
    if new:
        period_callback_id = curdoc().add_periodic_callback(auto_update, 1000)
        message_show.text = "状态:启动自动刷新"
    else:
        curdoc().remove_periodic_callback(period_callback_id)
        period_callback_id = None
        time_count = 0
        message_show.text = "状态:取消自动刷新"


def get_chart():
    global layout
    layout = gridplot([[main_ax, space_grav_ax], [time_grav_ax, tool_ax]], merge_tools=False)


end_time = TimeTool.get_now_time(return_type='datetime')
start_time = TimeTool.get_start_time(end_time, days=365+365)
code = Code('999999', frequency=ANALYZE_FREQ, start_time=start_time, end_time=end_time)

get_analyze_data(code)
create_main_ax()
create_time_grav_ax()
create_space_grav_ax()
create_tool_ax()

draw_main_ax()
draw_time_grav_dist()
draw_space_grav_dist()
configure_tools()

get_chart()
curdoc().add_root(layout)
curdoc().title = "Analyze - 999999"
