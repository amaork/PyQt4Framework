# -*- coding: utf-8 -*-
import math
from PySide.QtGui import *
from PySide.QtCore import *
import framework.misc.windpi as dpi
from framework.core.datatype import *
from framework.misc.settings import *
from framework.gui.widget import PaintWidget
from framework.gui.container import ComponentManager
__all__ = ['SampleSelectInput', 'VirtualNumberKeyboard', 'VirtualNumberInput', 'VolumeSelectInput']


class SampleSelectInput(PaintWidget):
    MARGIN = 5
    DEFAULT_FONT = "Times New Roman"
    DEFAULT_OVER_COLOR = Qt.lightGray
    DEFAULT_BG_COLOR = QColor(0x5d, 0x4e, 0x60)

    sampleSelected = Signal(object)

    def __init__(self, diameter=400, numbers=12, font_name=DEFAULT_FONT, parent=None):
        super(SampleSelectInput, self).__init__(parent)

        self.state = ""
        self.numbers = numbers
        self.move_over_idx = -1
        self.current_selected = 0
        self.font_name = font_name
        self.bg_color = self.DEFAULT_BG_COLOR
        self.__updatePanelDiameter(diameter)
        self.sample_poses = dict()
        self.__scale_factor = max(dpi.get_program_scale_factor())
        self.__scale_x, self.__scale_y = dpi.get_program_scale_factor()
        self.sample_angles = [0]
        single_sample_angle = 360 / numbers
        for i in range(1, numbers):
            self.sample_angles.append(360 - single_sample_angle * i)
        self.setMouseTracking(True)

    def __updatePanelDiameter(self, diameter):
        self.outer_ring_diameter = diameter - self.MARGIN * 2
        self.outer_ring_radius = self.outer_ring_diameter / 2

        self.inner_ring_diameter = self.outer_ring_diameter * 0.618
        self.inner_ring_radius = self.inner_ring_diameter / 2

        self.middle_ring_diameter = self.inner_ring_diameter + (self.outer_ring_diameter - self.inner_ring_diameter) / 2
        self.middle_ring_radius = self.middle_ring_diameter / 2

        self.sample_diameter = math.pi * self.middle_ring_diameter / (self.numbers + 2)
        self.sample_radius = self.sample_diameter / 2

        self.center = QPoint(self.MARGIN + self.outer_ring_radius, self.MARGIN + self.outer_ring_radius)
        self.update()

    @staticmethod
    def angle_to_pos(radius, angle):
        pg = angle * math.pi / 180.0
        return radius * math.cos(pg), radius * math.sin(pg)

    def get_font_size(self, diameter, number):
        number_text_length = len("{}".format(number))
        return min(diameter / number_text_length / 0.618, diameter * 0.618) / self.__scale_factor

    def setState(self, st):
        if isinstance(st, str):
            self.state = st
            self.update()

    def getState(self, st):
        return self.state

    def setThemeColor(self, color):
        if not isinstance(color, QColor):
            return

        self.bg_color = color
        self.update()

    def getSelectLocation(self):
        return self.current_selected + 1

    def setSelectLocation(self, loc):
        if 1 <= loc <= 12:
            self.current_selected = loc - 1
            self.update()

    def getSelectedNumber(self, point):
        for number, rect in self.sample_poses.items():
            if rect.contains(point):
                return number - 1

        return -1

    def paintEvent(self, ev):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont(self.font_name, self.get_font_size(self.sample_diameter, self.numbers))

        # Draw outer ring
        painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(QBrush(self.bg_color, Qt.SolidPattern))
        painter.drawEllipse(self.MARGIN, self.MARGIN, self.outer_ring_diameter, self.outer_ring_diameter)

        # Draw inner-ring
        painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))
        painter.drawEllipse(self.center, self.inner_ring_radius, self.inner_ring_radius)

        if self.state:
            fm = QFontMetrics(font)
            painter.setPen(self.bg_color)
            painter.setFont(font)
            painter.drawText(self.MARGIN + self.outer_ring_diameter / 2 - fm.width(self.state) / 2,
                             self.MARGIN + self.outer_ring_diameter / 2 + fm.height() / 3,
                             self.tr(self.state))

        # Draw sample
        self.sample_poses.clear()
        w = self.inner_ring_diameter
        s = self.MARGIN + self.sample_diameter
        self.sample_poses[0] = QRect(s, s, w, w)
        for idx, angel in enumerate(self.sample_angles):
            r = self.middle_ring_radius
            x, y = self.angle_to_pos(r, angel)
            x = self.center.x() + x - self.sample_radius
            y = self.center.y() + y - self.sample_radius
            self.sample_poses[idx + 1] = QRect(x, y, self.sample_diameter, self.sample_diameter)

            # Draw sample
            if self.move_over_idx == idx or self.current_selected == idx:
                color = self.DEFAULT_OVER_COLOR
            else:
                color = self.bg_color.darker()

            # rg = QRadialGradient()
            # rg.setColorAt(0.0, Qt.white)
            # rg.setColorAt(0.2, Qt.green)
            # rg.setColorAt(0.8, Qt.gray)
            # painter.setBrush(QBrush(rg))
            painter.setBrush(QBrush(color, Qt.SolidPattern))
            painter.drawEllipse(x, y, self.sample_diameter, self.sample_diameter)

            # Draw sample text
            painter.setPen(self.bg_color)
            painter.setFont(font)
            painter.drawText(x, y, self.sample_diameter, self.sample_diameter, Qt.AlignCenter, "{}".format(idx + 1))

    def resizeEvent(self, ev):
        width = ev.size().width()
        height = ev.size().height()
        self.__updatePanelDiameter(min(width, height))

    def mouseMoveEvent(self, ev):
        self.move_over_idx = self.getSelectedNumber(ev.pos())
        self.update()

    def mouseReleaseEvent(self, ev):
        if ev.button() != Qt.LeftButton:
            return

        number = self.getSelectedNumber(ev.pos())
        if number != -1:
            self.current_selected = number
            self.sampleSelected.emit(number + 1)
            # TODO: Add animation
            # print(number + 1)
            self.update()

    def enterEvent(self, ev):
        pass

    def leaveEvent(self, ev):
        self.move_over_idx = -1
        self.update()


class VolumeSelectInput(QRadioButton):
    DEFAULT_FG_COLOR = Qt.lightGray
    DEFAULT_BG_COLOR = QColor(0x5d, 0x4e, 0x60)

    def __init__(self, text, width=60, height=150, cap_height=25, parent=None):
        super(VolumeSelectInput, self).__init__(parent)
        self.clicked.connect(self.slotChecked)

        self.text = text
        self.__fg_color = self.DEFAULT_FG_COLOR
        self.__bg_color = self.DEFAULT_BG_COLOR
        self.__scale_factor = max(dpi.get_program_scale_factor())
        self.__scale_x, self.__scale_y = dpi.get_program_scale_factor()
        self.__updateSize(width, height, cap_height)

    def sizeHint(self):
        return QSize(self.__width, self.__height + self.__cap_height * 2)

    def __updateSize(self, width, height, cap_height):
        self.__width = width * self.__scale_x
        self.__height = height * self.__scale_y
        self.__cap_height = cap_height
        self.__neck_height = self.__cap_height - 5
        self.__neck_width = self.__width * 0.618
        self.__neck_y_start = self.__neck_height
        self.update()

    def paintEvent(self, ev):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.isChecked():
            bg, fg = self.__bg_color, self.__fg_color
        else:
            bg, fg = self.__fg_color, self.__bg_color

        painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(QBrush(bg, Qt.SolidPattern))
        painter.drawRoundedRect(0, 0, self.__width, self.__cap_height, 5.0, 5.0)
        painter.drawRoundedRect(self.__width / 5, self.__cap_height - 10,
                                self.__width / 5 * 3, self.__neck_height * 2, 5.0, 5.0)
        painter.drawRoundedRect(QRectF(0.0, self.__cap_height * 1.5, self.__width, self.__height), 5.0, 5.0)

        painter.setPen(QPen(QColor(fg)))
        painter.setFont(QFont("Times New Roman", self.__width / 3 / self.__scale_factor))
        painter.drawText(self.rect(), Qt.AlignLeft | Qt.AlignVCenter, self.text)

    def slotChecked(self):
        self.setChecked(True)

    def mousePressEvent(self, ev):
        self.clicked.emit()

    def setThemeColor(self, color):
        if not isinstance(color, QColor):
            return

        self.__bg_color = color
        self.update()

    # def resizeEvent(self, ev):
    #     print(ev.size())
    #     self.__updateSize(ev.size().width(), ev.size().height())


class VirtualNumberInput(QLineEdit):
    numberChanged = Signal(object)
    themeColor = QColor(93, 78, 96)

    def __init__(self, initial_value=0, min_=0, max_=9999, decimals=0, parent=None):
        super(VirtualNumberInput, self).__init__(parent)
        self.setReadOnly(True)
        self.setValidator(QIntValidator(min_, max_))
        self.setText("{}".format(initial_value))
        self.setProperty("min", min_)
        self.setProperty("max", max_)
        self.setProperty("decimals", decimals)

    @classmethod
    def setThemeColor(cls, color):
        if not isinstance(color, QColor):
            return

        cls.themeColor = color

    def mousePressEvent(self, ev):
        if ev.button() != Qt.LeftButton:
            return

        input_min = self.property("min")
        input_max = self.property("max")
        input_decimals = self.property("decimals")
        if not input_decimals:
            value = VirtualNumberKeyboard.getInt(min_=input_min, max_=input_max,
                                                 theme_color=VirtualNumberInput.themeColor, parent=self)
        else:
            value = VirtualNumberKeyboard.getDouble(min_=input_min, max_=input_max, decimals=input_decimals,
                                                    theme_color=VirtualNumberInput.themeColor, parent=self)
        if value is not None:
            self.setText(str(value))
            self.numberChanged.emit(value)


class VirtualKeyboard(QDialog):
    KEY_MAP = ()
    KeyPressed = Signal(object)

    def __init__(self, parent=None):
        super(VirtualKeyboard, self).__init__(parent)


class VirtualNumberKeyboard(VirtualKeyboard):
    KEY_MAP = (

        ("Min", "Max", "C"),
        ("7", "8", "9"),
        ("4", "5", "6"),
        ("1", "2", "3"),
        ("0", ".", "+/-"),
        ("<-", "确定", "取消"),
    )

    INT_KEY_MAP = (

        ("Min", "Max", "C"),
        ("7", "8", "9"),
        ("4", "5", "6"),
        ("1", "2", "3"),
        ("0", "确定", "取消"),
    )

    MIN_WIDTH = 250
    MIN_HEIGHT = 324
    FONT_BASE_SIZE = 20
    DEF_FONT_NAME = "等线 Light"
    DISPLAY_FONT_SIZE = FONT_BASE_SIZE * 1.5

    def __init__(self, min_=0, max_=100, initial_value=0, decimals=0,
                 key_map=KEY_MAP, theme_color=VirtualNumberInput.themeColor, parent=None):
        super(VirtualNumberKeyboard, self).__init__(parent)

        self.timer_cnt = 0
        self.min_number = min_
        self.max_number = max_
        self.key_map = key_map
        self.number_decimals = decimals

        self.old_display = ""
        self.current_display = ""
        self.overflow_flag = False
        self.initial_value = initial_value
        self.__scale_factor = max(dpi.get_program_scale_factor())

        self.fg_color = (255, 255, 255)
        self.rg_color = (0x96, 0xf7, 0x51)
        try:
            self.bg_color = (theme_color.red(), theme_color.green(), theme_color.blue())
        except AttributeError:
            self.bg_color = VirtualNumberInput.themeColor

        self.rg_color = UiColorInput.get_color_stylesheet(self.rg_color)
        self.fg_color = UiColorInput.get_color_stylesheet(self.fg_color)
        self.bg_color = UiColorInput.get_bg_color_stylesheet(self.bg_color)
        self.overflow_color = UiColorInput.get_color_stylesheet((255, 0, 0))

        self.__initUi()
        self.__initData()
        self.__initStyle()
        self.__initSignalAndSlots()
        self.clrOverflow()
        self.startTimer(600)

    def __initUi(self):
        self.ui_display = QLineEdit()

        key_layout = QGridLayout()
        for row, row_keys in enumerate(self.key_map):
            for column, key in enumerate(row_keys):
                btn = QPushButton(key)
                btn.clicked.connect(self.slotNumberClicked)
                btn.setProperty("name", key)
                btn.setProperty("value", key)
                btn.setMinimumHeight(50 * self.__scale_factor)
                btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
                key_layout.addWidget(btn, row, column)

        layout = QVBoxLayout()
        layout.addWidget(self.ui_display)
        layout.addLayout(key_layout)
        self.setLayout(layout)
        self.ui_manager = ComponentManager(layout)

    def __initData(self):
        self.ui_display.setText(str(self.initial_value))
        self.ui_min = self.ui_manager.getByValue("name", "Min", QPushButton)
        self.ui_max = self.ui_manager.getByValue("name", "Max", QPushButton)
        self.ui_min.setText("{}".format(self.min_number))
        self.ui_max.setText("{}".format(self.max_number))

    def __initStyle(self):
        self.ui_display.setReadOnly(True)
        self.ui_display.setAlignment(Qt.AlignRight)
        self.ui_display.setMinimumHeight(self.FONT_BASE_SIZE * 4 * self.__scale_factor)
        self.ui_display.setMaxLength(len("{}".format(self.max_number)) + self.number_decimals + 1)

        meter = QFontMetrics(QFont("等线 Light", self.DISPLAY_FONT_SIZE * self.__scale_factor))
        self.ui_display.setMinimumWidth(meter.width("0" * self.ui_display.maxLength() + "-."))

        [item.setStyleSheet(self.rg_color) for item in (self.ui_min, self.ui_max)]

        self.setStyleSheet('font: {}pt "宋体"; {};{};'.format(
            self.FONT_BASE_SIZE, self.bg_color, self.fg_color)
        )

        # self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

    def __initSignalAndSlots(self):
        ok = self.ui_manager.getByValue("name", "确定", QPushButton)
        cancel = self.ui_manager.getByValue("name", "取消", QPushButton)
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)

    def __flush(self):
        self.ui_display.setText(self.current_display)

    def __checkValue(self):
        return self.min_number <= str2float(self.current_display) <= self.max_number

    def sizeHint(self):
        meter = QFontMetrics(QFont(self.DEF_FONT_NAME, self.FONT_BASE_SIZE))
        width = meter.width(str(self.min_number) + str(self.max_number) + "  C  ")
        return QSize(width * self.__scale_factor, meter.height() * len(self.key_map) * self.__scale_factor)

    def setOverflow(self):
        self.overflow_flag = True
        self.ui_display.setStyleSheet("font: {}pt '等线 Light'; {};{};".format(
            self.DISPLAY_FONT_SIZE * self.__scale_factor, self.ui_display.styleSheet(), self.overflow_color)
        )

    def clrOverflow(self):
        self.overflow_flag = False
        self.ui_display.setStyleSheet("font: {}pt '等线 Light'; {};{};".format(
            self.DISPLAY_FONT_SIZE * self.__scale_factor, self.ui_display.styleSheet(), self.fg_color)
        )

    def callbackCheckOverflow(self):
        v = str2float(self.ui_display.text())
        if v > self.max_number or v < self.min_number and v != 0:
            self.current_display = self.old_display
            self.setOverflow()
            self.__flush()
            return

    def slotNumberClicked(self):
        key = self.sender()
        value = key.property("value")
        new_value = self.current_display
        if value in map(str, range(0, 10)):
            if value == "0" and self.current_display == "0":
                return

            try:
                new_value += value
                dot_pos = self.current_display.index(".")
                if len(new_value[dot_pos + 1:]) > self.number_decimals:
                    return
            except ValueError:
                pass

        elif value == "Max":
            new_value = str(self.max_number)
        elif value == "Min":
            new_value = str(self.min_number)
        elif value == "C":
            new_value = ""
            self.old_display = ""
        elif value == ".":
            if self.number_decimals <= 0:
                return

            if "." in self.current_display:
                return

            if len(self.current_display) == 0:
                new_value = "0."
            else:
                new_value += "."

        elif value == "+/-":
            if self.current_display.startswith("-"):
                new_value = self.current_display[1:]
            else:
                new_value = "-" + self.current_display
        elif value == "<-":
            if not len(self.current_display):
                return

            new_value = self.current_display[:-1]
        else:
            return

        self.current_display = new_value
        if self.__checkValue():
            self.old_display = self.current_display

        self.__flush()

    def getIntValue(self):
        if self.result():
            try:
                v = int(self.current_display, 10)
            except ValueError:
                v = 0
            return v if self.min_number <= v <= self.max_number else str2number(self.old_display)

    def getDoubleValue(self):
        if self.result():
            v = str2float(self.current_display)
            return v if self.min_number <= v <= self.max_number else str2float(self.old_display)

    def timerEvent(self, ev):
        self.timer_cnt += 1

        if self.overflow_flag:
            self.clrOverflow()
            self.current_display = self.old_display
            self.__flush()
            return

        if self.timer_cnt % 2 == 0:
            v = str2float(self.current_display)
            if v > self.max_number or v < self.min_number and v != 0:
                self.setOverflow()
                return

    @classmethod
    def getInt(cls, min_=0, max_=3600, initial_value=0,
               key_map=KEY_MAP, theme_color=VirtualNumberInput.themeColor, parent=None):
        dialog = cls(min_, max_, initial_value, 0, key_map, theme_color, parent)
        dialog.exec_()
        return dialog.getIntValue()

    @classmethod
    def getDouble(cls, min_=0, max_=100.0, decimals=1, initial_value=0,
                  key_map=KEY_MAP, theme_color=VirtualNumberInput.themeColor, parent=None):
        dialog = cls(min_, max_, initial_value, decimals, key_map, theme_color, parent)
        dialog.exec_()
        return dialog.getDoubleValue()