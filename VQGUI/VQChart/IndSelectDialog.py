from PySide6.QtWidgets import QDialog

from VQGUI.VQChart.ui_IndSelectDialog import Ui_IndSelectDialog


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
