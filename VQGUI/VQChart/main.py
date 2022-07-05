from typing import Union

from VQGUI.VQChart import MainChart, ChartWidget
import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QMainWindow, QInputDialog, QLineEdit, QDialog
import sys
import numpy as np

from VQGUI.VQChart.IndicatorChart import IndicatorChart
from VQGUI.VQChart.Params import CURSOR_COLOR, BLACK_COLOR
from VisionQuant.Analysis.Relativity.Relativity import Relativity
from VisionQuant.utils import TimeTool
from VisionQuant.utils.Code import Code
from VisionQuant.utils.Params import Freq
from VQGUI.VQChart.ui_MainWindow import Ui_MainWindow
from VQGUI.VQChart.ui_IndSelectDialog import Ui_IndSelectDialog
from VQGUI.VQChart.DataProtocol import line_data_protocol, vpvr_data_protocol, now_price_protocol, \
    indicator_protocol

DEFAULT_DAYS = 30


def get_analyze_data(_code):
    strategy_obj = Relativity(code=_code, show_result=False)
    strategy_obj.analyze()
    if strategy_obj.analyze_flag:
        ana_result = strategy_obj
        return 1, ana_result
    else:
        return 0, None


class GetAnalyzeDataThread(QThread):
    result: Signal = Signal(dict)

    def __init__(self):
        super().__init__()
        self.code = None
        self.callback = None

    def configure(self, code, callback):
        self.code = code
        self.callback = callback

    def run(self):
        ret, ana_result = get_analyze_data(self.code)
        self.result.emit({'ret': ret, 'ana_result': ana_result, 'callback': self.callback})


class IndSelectDialog(QDialog):
    def __init__(self):
        super(IndSelectDialog, self).__init__()
        self.ui = Ui_IndSelectDialog()
        self.ui.setupUi(self)
        self.ind_dict = dict()

    def init(self, ind_list):
        for index, ind_name in enumerate(ind_list):
            self.ind_dict[index] = ind_name
        self.ui.comboBox.addItems(ind_list)

    def get_value(self):
        self.show()
        if self.exec() == self.Accepted:
            index = self.ui.comboBox.currentIndex()
            return self.ind_dict[index], True
        else:
            return None, False


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.chart_widget = self.ui.graphicsView
        self.timer = QTimer(self)
        self.auto_update_flag = False
        self.get_data_thread = GetAnalyzeDataThread()
        self.now_time_label = QLabel(text="当前时间 {} ".format(TimeTool.get_now_time(return_type='str')))
        self.tick_timer = QTimer(self)
        self.ui.statusbar.addPermanentWidget(self.now_time_label)
        self._init_chart_flag = False
        self._level = None
        self._interval = None
        self._current_ind_name = None
        self.init()

    def init(self):
        self.ui.action_OpenChart.triggered.connect(self.set_code)
        self.ui.action_AutoUpdateChart.triggered.connect(self.set_update)
        self.ui.action_VPVRshow.triggered.connect(self.on_action_VPVRshow_triggered)
        self.ui.action_UnitVPVRshow.triggered.connect(self.on_action_UnitVPVRshow_triggered)
        self.ui.action_VPVRStatic.triggered.connect(self.on_action_VPVRStatic_triggered)
        self.ui.action_VPVRdynamic.triggered.connect(self.on_action_VPVRdynamic_triggered)
        self.ui.action_UnitVPVRByTime.triggered.connect(self.on_action_UnitVPVRByTime_triggered)
        self.ui.action_UnitVPVRByLevel.triggered.connect(self.on_action_UnitVPVRByLevel_triggered)
        self.ui.action_UnitVPVRByDay.triggered.connect(self.on_action_UnitVPVRByDay_triggered)
        self.ui.action_UnitVPVRByLevel4.triggered.connect(self.on_action_UnitVPVRByLevel4_triggered)
        self.ui.action_ShowIndChart.triggered.connect(self.on_action_ShowIndChart_triggered)
        self.ui.action_HideIndChart.triggered.connect(self.on_action_HideIndChart_triggered)
        self.ui.action_SelectInd.triggered.connect(self.on_action_SelectInd_triggered)
        self.timer.timeout.connect(self.update_widget)
        self.tick_timer.timeout.connect(self.now_time_update)
        self.get_data_thread.result.connect(self._on_analyze_finished)
        self.tick_timer.start(1000)

    def on_action_ShowIndChart_triggered(self):
        if self.chart_widget.get_plot('indicator'):
            self.chart_widget.get_plot('indicator').show()
        else:
            indicator_plot = IndicatorChart()
            self.chart_widget.add_plot(plot_name='indicator', plot=indicator_plot)
        self.ui.action_SelectInd.setEnabled(True)

    def on_action_HideIndChart_triggered(self):
        if self.chart_widget.get_plot('indicator'):
            self.chart_widget.get_plot('indicator').hide()
        self.ui.action_SelectInd.setEnabled(False)

    def on_action_SelectInd_triggered(self):
        dialog = IndSelectDialog()
        dialog.init(self.chart_widget.analyze_result.get_all_indicators_name())
        ind_name, OK = dialog.get_value()
        if OK:
            data = self._indicator_protocol(ind_name)
            self.show_indicator(data)
            self._current_ind_name = ind_name

    def _indicator_protocol(self, ind_name):
        if ind_name == '累积成交量':
            return indicator_protocol(self.chart_widget.analyze_result, ind_name, ma=[240])
        if ind_name == '买卖成交量':
            return indicator_protocol(self.chart_widget.analyze_result, ind_name, ma=30)
        if ind_name == 'VMACD':
            return indicator_protocol(self.chart_widget.analyze_result, ind_name, ma_fast=1, ma_slow=3, ma_dea=3)
        if ind_name == 'DP':
            return indicator_protocol(self.chart_widget.analyze_result, ind_name, ma=[240])
        if ind_name == 'BSDP':
            return indicator_protocol(self.chart_widget.analyze_result, ind_name, ma=30)
        if ind_name == 'DPMACD':
            return indicator_protocol(self.chart_widget.analyze_result, ind_name, ma_fast=1, ma_slow=3, ma_dea=3)

    def on_action_VPVRshow_triggered(self):
        flag = self.ui.action_VPVRshow.isChecked()
        if flag:
            self.ui.action_VPVRStatic.setEnabled(True)
            self.ui.action_VPVRdynamic.setEnabled(True)
            items_name = self.chart_widget.main_chart.items_dict.keys()
            if 'vpvr' in items_name:
                self.chart_widget.main_chart.items_dict['vpvr'].show()
            else:
                self._show_VPVR_data(self.chart_widget.analyze_result)
        else:
            self.ui.action_VPVRStatic.setEnabled(False)
            self.ui.action_VPVRdynamic.setEnabled(False)
            self.chart_widget.main_chart.items_dict['vpvr'].hide()

    def on_action_UnitVPVRshow_triggered(self):
        flag = self.ui.action_UnitVPVRshow.isChecked()
        if flag:
            if self._interval is None:
                self._interval = 240
            self.ui.action_UnitVPVRByTime.setEnabled(True)
            self.ui.action_UnitVPVRByLevel.setEnabled(True)
            self.ui.action_UnitVPVRByDay.setEnabled(True)
            self.ui.action_UnitVPVRByLevel4.setEnabled(True)
            ana_result = self.chart_widget.analyze_result
            x_range_list = self._get_UnitVPVR_data_xrange_list(ana_result, interval=self._interval)
            self._show_UnitVPVR_data(ana_result, x_range_list)
        else:
            self._level = None
            self.ui.action_UnitVPVRByTime.setEnabled(False)
            self.ui.action_UnitVPVRByLevel.setEnabled(False)
            self.ui.action_UnitVPVRByDay.setEnabled(False)
            self.ui.action_UnitVPVRByLevel4.setEnabled(False)
            items_name = tuple(filter(lambda x: 'vpvr_' in x, self.chart_widget.main_chart.items_dict.keys()))
            for item_name in items_name:
                self.chart_widget.main_chart.remove_item(item_name)

    def on_action_UnitVPVRByTime_triggered(self):

        dialogTitle = "输入对话框"
        textLabel = "请输入分钟间隔"
        default_value = 240
        min_value = 30
        max_value = 1200
        step_value = 30
        interval, OK = QInputDialog.getInt(self, dialogTitle, textLabel, default_value,
                                           min_value, max_value, step_value)
        if OK:
            self._level = None
            self._interval = interval
            items_name = tuple(filter(lambda x: 'vpvr_' in x, self.chart_widget.main_chart.items_dict.keys()))
            for item_name in items_name:
                self.chart_widget.main_chart.remove_item(item_name)
            ana_result = self.chart_widget.analyze_result
            x_range_list = self._get_UnitVPVR_data_xrange_list(ana_result, interval=self._interval)
            self._show_UnitVPVR_data(ana_result, x_range_list)

    def on_action_UnitVPVRByLevel_triggered(self):
        dialogTitle = "输入对话框"
        textLabel = "请输入级别"
        default_value = 4
        min_value = 2
        max_value = 6
        step_value = 1
        level, OK = QInputDialog.getInt(self, dialogTitle, textLabel, default_value, min_value, max_value, step_value)
        if OK:
            self._level = level
            self._interval = None
            items_name = tuple(filter(lambda x: 'vpvr_' in x, self.chart_widget.main_chart.items_dict.keys()))
            for item_name in items_name:
                self.chart_widget.main_chart.remove_item(item_name)
            ana_result = self.chart_widget.analyze_result
            x_range_list = self._get_UnitVPVR_data_xrange_list(ana_result, level=self._level)
            self._show_UnitVPVR_data(ana_result, x_range_list)

    def on_action_UnitVPVRByDay_triggered(self):
        self._interval = 240
        self._level = None
        items_name = tuple(filter(lambda x: 'vpvr_' in x, self.chart_widget.main_chart.items_dict.keys()))
        for item_name in items_name:
            self.chart_widget.main_chart.remove_item(item_name)
        ana_result = self.chart_widget.analyze_result
        x_range_list = self._get_UnitVPVR_data_xrange_list(ana_result, interval=self._interval)
        self._show_UnitVPVR_data(ana_result, x_range_list)

    def on_action_UnitVPVRByLevel4_triggered(self):
        self._level = 4
        self._interval = None
        items_name = tuple(filter(lambda x: 'vpvr_' in x, self.chart_widget.main_chart.items_dict.keys()))
        for item_name in items_name:
            self.chart_widget.main_chart.remove_item(item_name)
        ana_result = self.chart_widget.analyze_result
        x_range_list = self._get_UnitVPVR_data_xrange_list(ana_result, level=self._level)
        self._show_UnitVPVR_data(ana_result, x_range_list)

    def on_action_VPVRStatic_triggered(self):
        items_name = self.chart_widget.main_chart.items_dict.keys()
        if 'vpvr' in items_name:
            self.chart_widget.main_chart.items_dict['vpvr'].show()
        else:
            self._show_VPVR_data(self.chart_widget.analyze_result)

        cursor = self.chart_widget.get_cursor()
        try:
            cursor.x_pos.disconnect(self._update_VPVR)
        except RuntimeError:
            pass
        self._update_VPVR(None)

    def on_action_VPVRdynamic_triggered(self):
        cursor = self.chart_widget.get_cursor()
        cursor.x_pos.connect(self._update_VPVR)

    def show_widget(self, ana_result):
        time_list = ana_result.kdata.data['time']
        self.chart_widget.init(ana_result.code, time_list, ana_result.code.frequency)

        show_data_list = []

        mc_res = []
        mc_res += line_data_protocol(ana_result)
        mc_res += now_price_protocol(ana_result)

        mc_res = self._get_VPVR_data(mc_res, ana_result)

        x_range_list = self._get_UnitVPVR_data_xrange_list(ana_result, interval=self._interval, level=self._level)
        mc_res = self._get_UnitVPVR_data(mc_res, ana_result, x_range_list)

        main_chart_dict = {'plot_name': 'main', 'data': mc_res}
        show_data_list.append(main_chart_dict)

        if self._current_ind_name is not None:
            indc_res = self._indicator_protocol(self._current_ind_name)
            indi_chart_dict = {'plot_name': 'indicator', 'data': indc_res}
            show_data_list.append(indi_chart_dict)

        self.chart_widget.show_plots(show_data_list)

    def show_indicator(self, res):
        self.chart_widget.clear_plot('indicator')
        show_data_list = []
        indc_res = res
        indi_chart_dict = {'plot_name': 'indicator', 'data': indc_res}
        show_data_list.append(indi_chart_dict)
        self.chart_widget.show_plots(show_data_list)

    def update_widget(self):
        code = self.chart_widget.code
        code.end_time = TimeTool.get_now_time()
        self.get_data_thread.configure(code, self._update_widget)
        self.chart_widget.code = code
        self.show_message("正在更新{}数据...更新时间{}".format(code.code, TimeTool.time_to_str(code.end_time)), 500)
        self.get_data_thread.start()

    @staticmethod
    def _get_UnitVPVR_data_xrange_list(ana_result, interval=240, level=None):
        if level is not None:
            points = ana_result.time_grav.get_points(level)
            index_list = points['index']
            length = len(index_list)
            x_range_list = []
            for i in range(1, length-1):
                start_index = index_list[i - 1]
                end_index = index_list[i]
                x_range_list.append((start_index, end_index))
            x_range_list.append((x_range_list[-1][1], ana_result.last_index + 1))
            return x_range_list
        else:
            if interval is None:
                return []
            x_range_list = []
            interval = interval // 30 * 30  # 设置为30的倍数
            start_index = ana_result.last_index // interval * interval - DEFAULT_DAYS * 240
            end_index = ana_result.last_index // interval * interval + 240
            for i in range(start_index, end_index, interval):
                x_range_list.append((i, i + interval))
            return x_range_list

    def _update_widget(self, ana_result):
        update_data_list = []
        mc_res = []
        mc_res += line_data_protocol(ana_result)
        mc_res += now_price_protocol(ana_result)

        mc_res = self._get_VPVR_data(mc_res, ana_result)

        x_range_list = self._get_UnitVPVR_data_xrange_list(ana_result, interval=self._interval, level=self._level)
        mc_res = self._get_UnitVPVR_data(mc_res, ana_result, x_range_list)
        main_chart_dict = {'plot_name': 'main', 'data': mc_res}
        update_data_list.append(main_chart_dict)
        if self._current_ind_name is not None:
            indc_res = self._indicator_protocol(self._current_ind_name)
            indi_chart_dict = {'plot_name': 'indicator', 'data': indc_res}
            update_data_list.append(indi_chart_dict)
        self.chart_widget.update_plots(update_data_list)

    def _get_VPVR_data(self, data_list, ana_result, end_index=None):
        if self.ui.action_VPVRshow.isChecked():
            data_list += vpvr_data_protocol(ana_result, x_range_list=[(None, end_index)], name_list=['vpvr'])
        return data_list

    def _show_VPVR_data(self, ana_result):
        show_data_list = []
        mc_res = []
        mc_res = self._get_VPVR_data(mc_res, ana_result)
        main_chart_dict = {'plot_name': 'main', 'data': mc_res}
        show_data_list.append(main_chart_dict)
        self.chart_widget.show_plots(show_data_list)

    def _get_UnitVPVR_data(self, data_list, ana_result, x_range_list):
        if self.ui.action_UnitVPVRshow.isChecked():
            name_list = []
            for x_range in x_range_list:
                name_list.append('vpvr_{}_{}'.format(*x_range))
            data_list += vpvr_data_protocol(ana_result, x_range_list=x_range_list, name_list=name_list)
        return data_list

    def _show_UnitVPVR_data(self, ana_result, x_range_list):
        show_data_list = []
        mc_res = []
        mc_res = self._get_UnitVPVR_data(mc_res, ana_result, x_range_list)
        main_chart_dict = {'plot_name': 'main', 'data': mc_res}
        show_data_list.append(main_chart_dict)
        self.chart_widget.show_plots(show_data_list)

    def _on_analyze_finished(self, res_data: dict):
        ret, ana_result, callback = res_data['ret'], res_data['ana_result'], res_data['callback']
        if ret:
            if not self._init_chart_flag:
                self._enable_buttons()
                self._init_chart_flag = True
            self.chart_widget.analyze_result = ana_result
            self.chart_widget.code = ana_result.code
            callback(ana_result)
            self.show_message("更新完成！".format(ana_result.code.code,
                                             TimeTool.time_to_str(ana_result.code.end_time)), 1000)

    def _update_VPVR(self, end_index: Union[int, None]):
        update_data_list = []
        mc_res = []
        mc_res = self._get_VPVR_data(mc_res, self.chart_widget.analyze_result, end_index)
        main_chart_dict = {'plot_name': 'main', 'data': mc_res}
        update_data_list.append(main_chart_dict)
        self.chart_widget.update_plots(update_data_list)

    def set_update(self):
        if self.auto_update_flag:
            self.timer.stop()
            self.show_message("停止自动更新数据...", 3000)
            self.ui.action_AutoUpdateChart.setText("开始自动更新")
            self.auto_update_flag = False
        else:
            self.timer.start(3000)
            self.show_message("开始自动更新数据...", 3000)
            self.ui.action_AutoUpdateChart.setText("停止自动更新")
            self.auto_update_flag = True

    def set_code(self):
        dialogTitle = "输入对话框"
        textLabel = "请输入代码"
        echomode = QLineEdit.EchoMode.Normal
        text, OK = QInputDialog.getText(self, dialogTitle, textLabel, echo=echomode)
        if OK:
            code = Code(text, end_time=TimeTool.get_now_time())
            if self.chart_widget.code is None or code.code != self.chart_widget.code.code:
                self.chart_widget.clear_plots()
                self.get_data_thread.configure(code, self.show_widget)
            else:
                self.get_data_thread.configure(code, self._update_widget)
            self.show_message("正在更新{}数据...更新时间{}".format(code.code, TimeTool.time_to_str(code.end_time)), 500)
            self.get_data_thread.start()

    def _enable_buttons(self):
        self.ui.action_AutoUpdateChart.setEnabled(True)
        self.ui.action_VPVRshow.setEnabled(True)
        self.ui.action_UnitVPVRshow.setEnabled(True)
        self.ui.action_ShowIndChart.setEnabled(True)
        self.ui.action_HideIndChart.setEnabled(True)
        # self.ui.action_VPVRStatic.setEnabled(True)
        # self.ui.action_VPVRdynamic.setEnabled(True)
        # self.ui.action_UnitVPVRByTime.setEnabled(True)
        # self.ui.action_UnitVPVRByLevel.setEnabled(True)

    def show_message(self, message, timeout):
        self.ui.statusbar.clearMessage()
        self.ui.statusbar.showMessage(message, timeout)

    def now_time_update(self):
        self.now_time_label.setText("当前时间 {} ".format(TimeTool.get_now_time(return_type='str')))


if __name__ == '__main__':
    # pg.exec()

    app = QApplication(sys.argv)
    window = MainWindow()

    # test_code = Code('002382', frequency=Freq.MIN1, start_time='2021-01-01 09:00:00',
    #                  end_time=TimeTool.get_now_time())
    # ret, data = get_analyze_data(test_code)
    # if ret:
    #     window.show_data(data)
    # else:
    #     raise Exception('未收到数据')

    window.show()

    sys.exit(app.exec())
