from PySide6.QtCore import QDateTime, QTime
from PySide6.QtWidgets import QDialog

from VQGUI.VQChart.ui_CodeInputDialog import Ui_CodeInputDialog
from VisionQuant.utils import TimeTool


class CodeInputDialog(QDialog):
    def __init__(self):
        super(CodeInputDialog, self).__init__()
        self.ui = Ui_CodeInputDialog()
        self.ui.setupUi(self)

    def init(self, is_update, start_time=None, end_time=None, **kwargs):
        if is_update:
            self.ui.localdataButton.setChecked(False)
            self.ui.newdataButton.setChecked(True)
        else:
            self.ui.localdataButton.setChecked(True)
            self.ui.newdataButton.setChecked(False)

        if 'code' in kwargs and kwargs['code'] is not None:
            self.ui.CodelineEdit.setText(kwargs['code'])

        if start_time is not None:
            time_str = TimeTool.time_to_str(start_time, '%Y-%m-%d %H:%M')
            self.ui.StartTimeEdit.setDateTime(QDateTime.fromString(time_str, 'yyyy-MM-dd HH:mm'))

        if end_time is not None:
            time_str = TimeTool.time_to_str(end_time, '%Y-%m-%d %H:%M')
            self.ui.EndTimeEdit.setDateTime(QDateTime.fromString(time_str, 'yyyy-MM-dd HH:mm'))
        else:
            tmp_end_time = QDateTime.currentDateTime()
            tmp_end_time.setTime(QTime.fromString('23:59', 'HH:mm'))
            self.ui.EndTimeEdit.setDateTime(tmp_end_time)

    def get_value(self):
        self.show()
        if self.exec() == self.Accepted:
            res = dict()
            res['code'] = self.ui.CodelineEdit.text()
            res['start_time'] = self.ui.StartTimeEdit.dateTime().toString('yyyy-MM-dd HH:mm')
            res['end_time'] = self.ui.EndTimeEdit.dateTime().toString('yyyy-MM-dd HH:mm')
            res['is_update'] = self._get_is_update_flag()
            print(res)
            return res, True
        else:
            return None, False

    def _get_is_update_flag(self):
        if self.ui.newdataButton.isChecked():
            return True
        else:
            return False
