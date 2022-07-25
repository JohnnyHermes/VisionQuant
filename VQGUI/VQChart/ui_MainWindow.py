# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MainWindow.ui'
##
## Created by: Qt User Interface Compiler version 6.3.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QFormLayout, QMainWindow, QSizePolicy,
    QStatusBar, QToolBar, QWidget)

from VQGUI.VQChart.ChartWidget import ChartWidget

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1440, 899)
        self.action_AutoUpdateChart = QAction(MainWindow)
        self.action_AutoUpdateChart.setObjectName(u"action_AutoUpdateChart")
        self.action_AutoUpdateChart.setEnabled(False)
        self.action_OpenChart = QAction(MainWindow)
        self.action_OpenChart.setObjectName(u"action_OpenChart")
        self.action_VPVRStatic = QAction(MainWindow)
        self.action_VPVRStatic.setObjectName(u"action_VPVRStatic")
        self.action_VPVRStatic.setEnabled(False)
        self.action_VPVRdynamic = QAction(MainWindow)
        self.action_VPVRdynamic.setObjectName(u"action_VPVRdynamic")
        self.action_VPVRdynamic.setEnabled(False)
        self.action_UnitVPVRshow = QAction(MainWindow)
        self.action_UnitVPVRshow.setObjectName(u"action_UnitVPVRshow")
        self.action_UnitVPVRshow.setCheckable(True)
        self.action_UnitVPVRshow.setEnabled(False)
        self.action_VPVRshow = QAction(MainWindow)
        self.action_VPVRshow.setObjectName(u"action_VPVRshow")
        self.action_VPVRshow.setCheckable(True)
        self.action_VPVRshow.setEnabled(False)
        self.action_UnitVPVRByTime = QAction(MainWindow)
        self.action_UnitVPVRByTime.setObjectName(u"action_UnitVPVRByTime")
        self.action_UnitVPVRByTime.setEnabled(False)
        self.action_UnitVPVRByLevel = QAction(MainWindow)
        self.action_UnitVPVRByLevel.setObjectName(u"action_UnitVPVRByLevel")
        self.action_UnitVPVRByLevel.setEnabled(False)
        self.action_UnitVPVRByDay = QAction(MainWindow)
        self.action_UnitVPVRByDay.setObjectName(u"action_UnitVPVRByDay")
        self.action_UnitVPVRByDay.setEnabled(False)
        self.action_UnitVPVRByLevel4 = QAction(MainWindow)
        self.action_UnitVPVRByLevel4.setObjectName(u"action_UnitVPVRByLevel4")
        self.action_UnitVPVRByLevel4.setEnabled(False)
        self.action_ShowIndChart = QAction(MainWindow)
        self.action_ShowIndChart.setObjectName(u"action_ShowIndChart")
        self.action_ShowIndChart.setEnabled(False)
        self.action_HideIndChart = QAction(MainWindow)
        self.action_HideIndChart.setObjectName(u"action_HideIndChart")
        self.action_HideIndChart.setEnabled(False)
        self.action_SelectInd = QAction(MainWindow)
        self.action_SelectInd.setObjectName(u"action_SelectInd")
        self.action_SelectInd.setEnabled(False)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.formLayout = QFormLayout(self.centralwidget)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.graphicsView = ChartWidget(self.centralwidget)
        self.graphicsView.setObjectName(u"graphicsView")
        self.graphicsView.setEnabled(True)

        self.formLayout.setWidget(0, QFormLayout.SpanningRole, self.graphicsView)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        self.statusbar.setSizeGripEnabled(False)
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QToolBar(MainWindow)
        self.toolBar.setObjectName(u"toolBar")
        self.toolBar.setEnabled(True)
        MainWindow.addToolBar(Qt.TopToolBarArea, self.toolBar)

        self.toolBar.addAction(self.action_OpenChart)
        self.toolBar.addAction(self.action_AutoUpdateChart)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.action_VPVRshow)
        self.toolBar.addAction(self.action_VPVRStatic)
        self.toolBar.addAction(self.action_VPVRdynamic)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.action_UnitVPVRshow)
        self.toolBar.addAction(self.action_UnitVPVRByTime)
        self.toolBar.addAction(self.action_UnitVPVRByLevel)
        self.toolBar.addAction(self.action_UnitVPVRByDay)
        self.toolBar.addAction(self.action_UnitVPVRByLevel4)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.action_ShowIndChart)
        self.toolBar.addAction(self.action_HideIndChart)
        self.toolBar.addAction(self.action_SelectInd)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.action_AutoUpdateChart.setText(QCoreApplication.translate("MainWindow", u"\u5f00\u59cb\u81ea\u52a8\u66f4\u65b0", None))
#if QT_CONFIG(tooltip)
        self.action_AutoUpdateChart.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>\u5f00\u59cb/\u505c\u6b62\u66f4\u65b0</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.action_OpenChart.setText(QCoreApplication.translate("MainWindow", u"\u6253\u5f00\u56fe\u8868", None))
        self.action_VPVRStatic.setText(QCoreApplication.translate("MainWindow", u"\u9759\u6001VPVR", None))
        self.action_VPVRdynamic.setText(QCoreApplication.translate("MainWindow", u"\u52a8\u6001VPVR", None))
        self.action_UnitVPVRshow.setText(QCoreApplication.translate("MainWindow", u"\u663e\u793aUnitVPVR", None))
        self.action_VPVRshow.setText(QCoreApplication.translate("MainWindow", u"\u663e\u793aVPVR", None))
        self.action_UnitVPVRByTime.setText(QCoreApplication.translate("MainWindow", u"\u6309\u65f6\u95f4\u5206\u9694", None))
        self.action_UnitVPVRByLevel.setText(QCoreApplication.translate("MainWindow", u"\u6309\u7ea7\u522b\u5206\u9694", None))
        self.action_UnitVPVRByDay.setText(QCoreApplication.translate("MainWindow", u"\u6309\u65e5\u5206\u9694", None))
        self.action_UnitVPVRByLevel4.setText(QCoreApplication.translate("MainWindow", u"\u6309\u7ea7\u522b4\u5206\u9694", None))
        self.action_ShowIndChart.setText(QCoreApplication.translate("MainWindow", u"\u663e\u793a\u6307\u6807\u56fe", None))
        self.action_HideIndChart.setText(QCoreApplication.translate("MainWindow", u"\u9690\u85cf\u6307\u6807\u56fe", None))
        self.action_SelectInd.setText(QCoreApplication.translate("MainWindow", u"\u9009\u62e9\u6307\u6807", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("MainWindow", u"toolBar", None))
    # retranslateUi

