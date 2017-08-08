# -*- coding: utf-8 -*-
from .button import RectButton
from .widget import SerialPortSettingWidget
from PySide.QtCore import Qt
from PySide.QtGui import QDialog, QColor, QLabel, QSpinBox, QSlider, QPushButton, QSplitter, \
    QVBoxLayout, QHBoxLayout, QGridLayout, QDialogButtonBox


__all__ = ['SimpleColorDialog', 'SerialPortSettingDialog']


class SimpleColorDialog(QDialog):
    def __init__(self, basic=False, color=Qt.black, parent=None):
        """Simple color dialog

        :param basic: if basic is true, only allow red, greed, blue, cyan, yellow, magenta, black, white color
        :param color: init color
        :param parent:
        :return:
        """
        super(SimpleColorDialog, self).__init__(parent)
        assert isinstance(color, (QColor, Qt.GlobalColor)), "Color TypeError:{0:s}".format(type(color))

        self.__initUi()
        self.__basic = basic
        self.__color = QColor(color)
        self.__updateColor(self.__color)

    def __initUi(self):
        # Color select buttons
        colorLayout = QGridLayout()
        colors = (Qt.black, Qt.red, Qt.blue, Qt.magenta, Qt.yellow, Qt.green, Qt.cyan, Qt.white)
        for row, depth in enumerate((255, 127, 64)):
            colorLayout.addWidget(QLabel("{0:d}".format(depth)), row, 0)
            for column, color in enumerate(colors):
                c = QColor(color)
                r, g, b = (depth if x else x for x in self.convertToRgb(c))
                c = QColor(r, g, b)
                button = RectButton(32, 24, color=(c, c))
                button.clicked.connect(self.slotChangeColor)
                colorLayout.addWidget(button, row, column + 1)

        # Color depth slider
        depthLayout = QHBoxLayout()
        self.__depth = QSlider(Qt.Horizontal)
        self.__depth.setRange(0, 255)
        self.__depth.setTickInterval(10)
        self.__depth.setTickPosition(QSlider.TicksBelow)
        self.__depth.valueChanged.connect(self.slotChangeDepth)
        depthLayout.addWidget(QLabel(self.tr("亮度")))
        depthLayout.addWidget(self.__depth)

        # Label for preview color
        self.__preview = QLabel()

        # Color value spinbox
        self.__red = QSpinBox()
        self.__green = QSpinBox()
        self.__blue = QSpinBox()
        valueLayout = QHBoxLayout()
        for text, spinbox in (("Red", self.__red), ("Green", self.__green), ("Blue", self.__blue)):
            valueLayout.addWidget(QLabel(text))
            valueLayout.addWidget(spinbox)
            spinbox.setRange(0, 255)
            spinbox.valueChanged.connect(self.slotChangeDepth)
            if text != "Blue":
                valueLayout.addWidget(QSplitter())

        # Dialog button
        button = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button.accepted.connect(self.accept)
        button.rejected.connect(self.reject)
        layout = QVBoxLayout()
        layout.addLayout(colorLayout)
        layout.addLayout(depthLayout)
        layout.addWidget(self.__preview)
        layout.addLayout(valueLayout)
        layout.addWidget(QSplitter())
        layout.addWidget(QSplitter())
        layout.addWidget(button)

        self.setLayout(layout)
        self.setWindowTitle(self.tr("请选择颜色"))

    def __getColor(self):
        """Get select color setting

        :return: r, g, b
        """
        return self.__color.red(), self.__color.green(), self.__color.blue()

    def __setColor(self, color):
        """Save color and update spinbox color

        :param color: select color
        :return: true or false
        """
        if not isinstance(color, QColor):
            return False

        self.__color = color
        self.__red.setValue(color.red())
        self.__blue.setValue(color.blue())
        self.__green.setValue(color.green())
        return True

    def __getCurrentColor(self):
        """Get ui spinbox color setting

        :return: r, g, b
        """
        r = self.__red.value()
        b = self.__blue.value()
        g = self.__green.value()
        return r, g, b

    def __updateColor(self, color):
        """Update ui elements setting

        :param color:
        :return:
        """
        if not isinstance(color, QColor):
            return

        self.__setColor(color)
        value = max(self.convertToRgb(color))
        self.slotChangeDepth(value)
        self.__depth.setValue(value)

        # Basic mode
        if self.__basic:
            r, g, b = self.__getColor()
            self.__red.setEnabled(r)
            self.__blue.setEnabled(b)
            self.__green.setEnabled(g)

    def slotChangeColor(self):
        btn = self.sender()
        if not isinstance(btn, RectButton):
            return

        # Update select color
        self.__updateColor(btn.getBrush().color())

    def slotChangeDepth(self, value):
        if self.__basic or self.sender() == self.__depth:
            r, g, b = self.__getColor()
            if r:
                self.__red.setValue(value)

            if g:
                self.__green.setValue(value)

            if b:
                self.__blue.setValue(value)

        r, g, b = self.__getCurrentColor()
        self.__preview.setStyleSheet("background:rgb({0:d},{1:d},{2:d})".format(r, g, b))

    def getSelectColor(self):
        if self.result():
            r, g, b = self.__getCurrentColor()
            return QColor(r, g, b)
        else:
            return self.__color

    @staticmethod
    def getColor(parent, color=Qt.red):
        panel = SimpleColorDialog(color=color, parent=parent)
        panel.exec_()
        return panel.getSelectColor()

    @staticmethod
    def getBasicColor(parent, color=Qt.red):
        panel = SimpleColorDialog(True, color, parent)
        panel.exec_()
        return panel.getSelectColor()

    @staticmethod
    def convertToRgb(color):
        if not isinstance(color, QColor):
            return 0, 0, 0

        return color.red(), color.green(), color.blue()

    @staticmethod
    def convertToIndexColor(color):
        if not isinstance(color, QColor):
            return 0, 0

        index = 0
        r, g, b = SimpleColorDialog.convertToRgb(color)

        if r:
            index |= 4

        if g:
            index |= 2

        if b:
            index |= 1

        return index, max(r, g, b)


class SerialPortSettingDialog(QDialog):
    def __init__(self, settings=SerialPortSettingWidget.DEFAULTS, remote="", parent=None):
        """Serial port configure dialog

        :param settings: serial port settings
        :param remote: scan remote serial port
        :param parent:
        """
        settings = settings or self.DEFAULTS
        super(SerialPortSettingDialog, self).__init__(parent)

        layout = QVBoxLayout()
        self.__widget = SerialPortSettingWidget(settings, remote)
        button = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button.accepted.connect(self.accept)
        button.rejected.connect(self.reject)

        layout.addWidget(self.__widget)
        layout.addWidget(QSplitter())
        layout.addWidget(button)

        self.setLayout(layout)
        self.setFixedSize(self.sizeHint())
        self.setWindowTitle(self.tr("串口配置对话框"))

    def getSerialSetting(self):
        if not self.result():
            return None

        return self.__widget.getSetting()

    @staticmethod
    def getSetting(parent, settings=SerialPortSettingWidget.DEFAULTS, remote=""):
        dialog = SerialPortSettingDialog(settings, remote, parent)
        dialog.exec_()
        return dialog.getSerialSetting()
