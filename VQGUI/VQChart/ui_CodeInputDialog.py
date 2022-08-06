# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'CodeInputDialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDateTimeEdit, QDialog,
    QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit,
    QRadioButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_CodeInputDialog(object):
    def setupUi(self, CodeInputDialog):
        if not CodeInputDialog.objectName():
            CodeInputDialog.setObjectName(u"CodeInputDialog")
        CodeInputDialog.resize(400, 220)
        self.buttonBox = QDialogButtonBox(CodeInputDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(100, 170, 181, 41))
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.horizontalLayoutWidget = QWidget(CodeInputDialog)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(90, 49, 231, 41))
        self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.localdataButton = QRadioButton(self.horizontalLayoutWidget)
        self.localdataButton.setObjectName(u"localdataButton")

        self.horizontalLayout.addWidget(self.localdataButton)

        self.newdataButton = QRadioButton(self.horizontalLayoutWidget)
        self.newdataButton.setObjectName(u"newdataButton")

        self.horizontalLayout.addWidget(self.newdataButton)

        self.verticalLayoutWidget = QWidget(CodeInputDialog)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(70, 90, 261, 80))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label = QLabel(self.verticalLayoutWidget)
        self.label.setObjectName(u"label")

        self.horizontalLayout_4.addWidget(self.label)

        self.StartTimeEdit = QDateTimeEdit(self.verticalLayoutWidget)
        self.StartTimeEdit.setObjectName(u"StartTimeEdit")
        self.StartTimeEdit.setDateTime(QDateTime(QDate(2008, 1, 1), QTime(0, 0, 0)))
        self.StartTimeEdit.setMinimumDateTime(QDateTime(QDate(2008, 1, 1), QTime(0, 0, 0)))
        self.StartTimeEdit.setCurrentSection(QDateTimeEdit.YearSection)
        self.StartTimeEdit.setCalendarPopup(True)

        self.horizontalLayout_4.addWidget(self.StartTimeEdit)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_2 = QLabel(self.verticalLayoutWidget)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_5.addWidget(self.label_2)

        self.EndTimeEdit = QDateTimeEdit(self.verticalLayoutWidget)
        self.EndTimeEdit.setObjectName(u"EndTimeEdit")
        self.EndTimeEdit.setDateTime(QDateTime(QDate(2008, 9, 14), QTime(0, 0, 0)))
        self.EndTimeEdit.setMinimumDate(QDate(2008, 1, 1))
        self.EndTimeEdit.setMaximumTime(QTime(23, 59, 59))
        self.EndTimeEdit.setCurrentSection(QDateTimeEdit.YearSection)
        self.EndTimeEdit.setCalendarPopup(True)

        self.horizontalLayout_5.addWidget(self.EndTimeEdit)


        self.verticalLayout.addLayout(self.horizontalLayout_5)

        self.horizontalLayoutWidget_4 = QWidget(CodeInputDialog)
        self.horizontalLayoutWidget_4.setObjectName(u"horizontalLayoutWidget_4")
        self.horizontalLayoutWidget_4.setGeometry(QRect(70, 20, 261, 31))
        self.horizontalLayout_6 = QHBoxLayout(self.horizontalLayoutWidget_4)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.label_3 = QLabel(self.horizontalLayoutWidget_4)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_6.addWidget(self.label_3)

        self.CodelineEdit = QLineEdit(self.horizontalLayoutWidget_4)
        self.CodelineEdit.setObjectName(u"CodelineEdit")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.CodelineEdit.sizePolicy().hasHeightForWidth())
        self.CodelineEdit.setSizePolicy(sizePolicy)

        self.horizontalLayout_6.addWidget(self.CodelineEdit)


        self.retranslateUi(CodeInputDialog)
        self.buttonBox.accepted.connect(CodeInputDialog.accept)
        self.buttonBox.rejected.connect(CodeInputDialog.reject)

        QMetaObject.connectSlotsByName(CodeInputDialog)
    # setupUi

    def retranslateUi(self, CodeInputDialog):
        CodeInputDialog.setWindowTitle(QCoreApplication.translate("CodeInputDialog", u"Dialog", None))
        self.localdataButton.setText(QCoreApplication.translate("CodeInputDialog", u"\u672c\u5730\u6570\u636e", None))
        self.newdataButton.setText(QCoreApplication.translate("CodeInputDialog", u"\u6700\u65b0\u6570\u636e", None))
        self.label.setText(QCoreApplication.translate("CodeInputDialog", u"\u5f00\u59cb\u65f6\u95f4", None))
        self.StartTimeEdit.setDisplayFormat(QCoreApplication.translate("CodeInputDialog", u"yyyy-MM-dd HH:mm", None))
        self.label_2.setText(QCoreApplication.translate("CodeInputDialog", u"\u7ed3\u675f\u65f6\u95f4", None))
        self.EndTimeEdit.setDisplayFormat(QCoreApplication.translate("CodeInputDialog", u"yyyy-MM-dd HH:mm", None))
        self.label_3.setText(QCoreApplication.translate("CodeInputDialog", u"\u54c1\u79cd\u4ee3\u7801", None))
    # retranslateUi

