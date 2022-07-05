# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'IndSelectDialog.ui'
##
## Created by: Qt User Interface Compiler version 6.3.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QSizePolicy, QWidget)

class Ui_IndSelectDialog(object):
    def setupUi(self, IndSelectDialog):
        if not IndSelectDialog.objectName():
            IndSelectDialog.setObjectName(u"IndSelectDialog")
        IndSelectDialog.resize(336, 178)
        self.buttonBox = QDialogButtonBox(IndSelectDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(70, 110, 171, 32))
        self.buttonBox.setToolTipDuration(-1)
        self.buttonBox.setLayoutDirection(Qt.LeftToRight)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.comboBox = QComboBox(IndSelectDialog)
        self.comboBox.setObjectName(u"comboBox")
        self.comboBox.setGeometry(QRect(40, 50, 251, 22))

        self.retranslateUi(IndSelectDialog)
        self.buttonBox.accepted.connect(IndSelectDialog.accept)
        self.buttonBox.rejected.connect(IndSelectDialog.reject)

        QMetaObject.connectSlotsByName(IndSelectDialog)
    # setupUi

    def retranslateUi(self, IndSelectDialog):
        IndSelectDialog.setWindowTitle(QCoreApplication.translate("IndSelectDialog", u"Dialog", None))
    # retranslateUi

